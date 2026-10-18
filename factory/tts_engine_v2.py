"""
tts_engine_v2.py - TTS ที่แก้แล้ว รองรับหลายตัว + fallback ดี
"""
import os
import asyncio
import subprocess
import tempfile

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except:
    EDGE_TTS_AVAILABLE = False

DEFAULT_VOICE = "th-TH-NiwatNeural"
ALTERNATE_VOICE = "th-TH-PremwadeeNeural"

def clean_text_for_tts(text):
    text = text.replace("。。。", " ").replace("...", " ")
    text = text.replace("#", " ")
    text = text.replace('"', '').replace("'", "")
    text = text.replace("**", "").replace("*", "")
    # ลบอีโมจิที่ TTS อ่านไม่ได้
    import re
    # ลบ emoji range
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    return text.strip()

async def _async_edge_tts(text, voice, output_path, rate="+0%", volume="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_path)

def generate_with_edge_tts(text, output_path, voice=DEFAULT_VOICE, rate="+0%", volume="+0%"):
    if not EDGE_TTS_AVAILABLE:
        return False, None
    text = clean_text_for_tts(text)
    if not text:
        return False, None
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    if os.path.exists(output_path):
        try: os.remove(output_path)
        except: pass
    try:
        asyncio.run(_async_edge_tts(text, voice, output_path, rate, volume))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            dur = get_audio_duration(output_path)
            print(f"[TTS][edge] ✅ {voice} {dur:.1f}s" if dur else f"[TTS][edge] ✅ {voice}")
            return True, dur
        return False, None
    except Exception as e:
        print(f"[TTS][edge] ❌ {e}")
        return False, None

def generate_with_gtts(text, output_path, lang='th'):
    """Fallback gTTS - ต้องมี internet แต่ลองดูก่อน"""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            dur = get_audio_duration(output_path)
            print(f"[TTS][gTTS] ✅ {lang} {dur:.1f}s" if dur else "[TTS][gTTS] ✅")
            return True, dur
    except Exception as e:
        print(f"[TTS][gTTS] ❌ {e}")
    return False, None

def generate_with_pyttsx3(text, output_path):
    """Offline TTS via pyttsx3 / espeak - ไม่ต้อง internet"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # ลองตั้งเสียงไทย ถ้ามี
        voices = engine.getProperty('voices')
        # เลือกเสียงแรกที่เจอ
        if voices:
            for v in voices:
                if 'thai' in v.name.lower() or 'th' in v.id.lower():
                    engine.setProperty('voice', v.id)
                    break
        engine.setProperty('rate', 150)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            dur = get_audio_duration(output_path)
            print(f"[TTS][pyttsx3] ✅ {dur:.1f}s" if dur else "[TTS][pyttsx3] ✅")
            return True, dur
    except Exception as e:
        print(f"[TTS][pyttsx3] ❌ {e}")
    return False, None

def generate_silent_tts(text, output_path, wpm=155):
    """
    Fallback สุดท้าย: สร้างไฟล์ silent ที่มี duration เท่ากับเวลาอ่าน
    ใช้เพื่อให้ video ไม่ silent และมี timing ถูกต้อง
    แล้วใช้แค่ background music
    """
    # ประมาณเวลาอ่าน: ไทย ~2.2 ตัวอักษรต่อคำ
    chars = len(text)
    words = max(10, chars / 2.2)
    seconds = (words / wpm) * 60
    seconds = max(8, min(58, seconds))
    print(f"[TTS][silent] ⏱️ Estimate {seconds:.0f}s for {chars} chars ({words:.0f} words)")

    try:
        # สร้าง silent audio ด้วย ffmpeg
        import shutil
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
                print(f"[TTS][silent] Using imageio ffmpeg: {ffmpeg}")
            except Exception as e:
                print(f"[TTS][silent] No ffmpeg found: {e}")
                return True, seconds
        if not ffmpeg or not os.path.exists(ffmpeg):
            print(f"[TTS][silent] ⚠️ No ffmpeg binary, return duration only")
            return True, seconds
        # ตรวจสอบ extension เพื่อเลือก codec ให้ถูก
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".mp3":
            cmd = [
                ffmpeg, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", f"{seconds:.1f}",
                "-acodec", "libmp3lame", "-q:a", "2",
                output_path
            ]
        else:
            cmd = [
                ffmpeg, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", f"{seconds:.1f}",
                "-acodec", "aac",
                output_path
            ]
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            print(f"[TTS][silent] ✅ Silent {seconds:.0f}s (will use music only)")
            return True, seconds
        print(f"[TTS][silent] ❌ ffmpeg failed: {result.stderr[:200] if result.stderr else 'no output'}")
        return True, seconds
    except Exception as e:
        print(f"[TTS][silent] ❌ {e}")
        import traceback
        traceback.print_exc()
        return False, seconds

def get_audio_duration(path):
    if not os.path.exists(path):
        return None
    try:
        from moviepy.editor import AudioFileClip
        c = AudioFileClip(path)
        d = c.duration
        c.close()
        return d
    except:
        try:
            from moviepy import AudioFileClip
            c = AudioFileClip(path)
            d = c.duration
            c.close()
            return d
        except:
            pass
    return None

def generate_tts(text, output_path, voice=DEFAULT_VOICE, rate="+0%", volume="+0%"):
    """
    Main TTS: ลอง edge-tts ก่อน ถ้าไม่ได้ให้ลอง gTTS, pyttsx3, สุดท้าย silent
    return: (success, duration)
    """
    text = clean_text_for_tts(text)
    if not text:
        return False, None

    # 1. edge-tts (ดีสุด เสียงไทยธรรมชาติ)
    ok, dur = generate_with_edge_tts(text, output_path, voice, rate, volume)
    if ok:
        return True, dur

    # ลองเสียงหญิง
    if voice == DEFAULT_VOICE:
        ok, dur = generate_with_edge_tts(text, output_path, ALTERNATE_VOICE, rate, volume)
        if ok:
            return True, dur

    # 2. gTTS (ต้อง internet แต่ลอง)
    ok, dur = generate_with_gtts(text, output_path, lang='th')
    if ok:
        return True, dur

    # 3. pyttsx3 offline
    ok, dur = generate_with_pyttsx3(text, output_path)
    if ok:
        return True, dur

    # 4. silent fallback - จะได้มี timing ถูกต้อง
    ok, dur = generate_silent_tts(text, output_path)
    if ok:
        # สร้างไฟล์ silent สำเร็จ หรือได้ duration
        # ถ้าไฟล์ silent มี ให้ return True, ถ้าไม่มี duration ก็ return True ให้ renderer ใช้ music only
        exists = os.path.exists(output_path) and os.path.getsize(output_path) > 100
        if exists:
            return True, dur
        else:
            # ไม่มีไฟล์ แต่มี duration ให้ caller รู้ว่า TTS ล้มเหลวแต่มี estimate
            # caller จะใช้ music only
            return False, dur
    return False, None

def estimate_duration(text, wpm=155):
    chars = len(text)
    words = max(10, chars / 2.2)
    seconds = (words / wpm) * 60
    return max(8, min(60, seconds))
