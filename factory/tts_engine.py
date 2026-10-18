"""
tts_engine.py - พากย์เสียงไทยอัตโนมัติ
"""
import os
import asyncio

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except:
    EDGE_TTS_AVAILABLE = False

DEFAULT_VOICE = "th-TH-NiwatNeural"
ALTERNATE_VOICE = "th-TH-PremwadeeNeural"

def clean_text_for_tts(text):
    """ล้างข้อความให้ TTS อ่านลื่น"""
    # ลบ emoji หนักๆ ที่อ่านไม่ออก
    # แต่เก็บสระไทยไว้
    text = text.replace("。。。", " ")
    text = text.replace("...", " ")
    # ลบ hashtag
    text = text.replace("#", " ")
    # แทนเลขไทย
    return text.strip()

async def _async_tts(text, voice, output_path, rate="+0%", volume="+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_path)

def generate_tts(text, output_path, voice=DEFAULT_VOICE, rate="+0%", volume="+0%"):
    """
    สร้างไฟล์เสียง TTS
    return: (success: bool, duration_seconds: float or None)
    """
    if not EDGE_TTS_AVAILABLE:
        print("[TTS] edge_tts not installed. pip install edge-tts")
        return False, None
    
    # เช็คเน็ตก่อน - ถ้า offline ให้ข้ามเลย
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
    except:
        pass  # ลองทำต่อไป ถ้าไม่ได้ให้ fail fast
    
    
    text = clean_text_for_tts(text)
    if not text:
        print("[TTS] Empty text")
        return False, None
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    try:
        # ลบไฟล์เก่า
        if os.path.exists(output_path):
            os.remove(output_path)
        
        asyncio.run(_async_tts(text, voice, output_path, rate, volume))
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            # วัดความยาวด้วย moviepy ถ้ามี
            duration = None
            try:
                from moviepy.editor import AudioFileClip
                clip = AudioFileClip(output_path)
                duration = clip.duration
                clip.close()
            except:
                try:
                    from moviepy import AudioFileClip
                    clip = AudioFileClip(output_path)
                    duration = clip.duration
                    clip.close()
                except:
                    pass
            
            print(f"[TTS] ✅ Generated: {output_path} ({duration:.1f}s)" if duration else f"[TTS] ✅ Generated: {output_path}")
            return True, duration
        else:
            print(f"[TTS] ❌ File too small or not created: {output_path}")
            return False, None
            
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return False, None

def tts_with_fallback_options(text, output_path):
    """ลองหลายเสียงถ้าตัวหลักล่ม"""
    voices = [DEFAULT_VOICE, ALTERNATE_VOICE, "th-TH-AcharaNeural", "en-US-AriaNeural"]
    for voice in voices:
        ok, dur = generate_tts(text, output_path, voice=voice)
        if ok:
            return True, dur, voice
    return False, None, None
