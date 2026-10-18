"""
human_tts.py - เสียงพากย์เหมือนคนจริง มีอารมณ์ มีจังหวะ
ใช้ SSML + การเว้นจังหวะ + เปลี่ยนอารมณ์ตามเนื้อหา
รองรับ: edge-tts (ฟรี, ไทยธรรมชาติที่สุด) + ElevenLabs (พรีเมี่ยม)
"""
import os
import re
import asyncio

try:
    import edge_tts
    EDGE_AVAILABLE = True
except:
    EDGE_AVAILABLE = False

# เสียงไทยที่แนะนำ (edge-tts)
# th-TH-NiwatNeural = ชาย ภูมิฐาน น่าเชื่อถือ เหมาะกับความรู้
# th-TH-PremwadeeNeural = หญิง อบอุ่น เป็นมิตร
# th-TH-AcharaNeural = หญิง วัยรุ่น สดใส

VOICE_PRESETS = {
    "knowledge_male": "th-TH-NiwatNeural",      # ผู้ชาย ให้ความรู้
    "knowledge_female": "th-TH-PremwadeeNeural", # ผู้หญิง อบอุ่น
    "young_female": "th-TH-AcharaNeural",         # วัยรุ่น
}

# SSML Rate/Pitch ตามอารมณ์
EMOTION_SSML = {
    "hook":   {"rate": "+8%", "pitch": "+6%", "desc": "ตื่นเต้น ชวนสงสัย"},
    "point1": {"rate": "+2%", "pitch": "+0%", "desc": "เล่าเรื่องปกติ"},
    "point2": {"rate": "+0%", "pitch": "+0%", "desc": "เน้นๆ ช้าลงนิด"},
    "point3": {"rate": "+1%", "pitch": "+2%", "desc": "เฉลย ดีใจขึ้น"},
    "cta":    {"rate": "-2%", "pitch": "+1%", "desc": "ชวนคุยเป็นกันเอง"},
}

def add_drama_pauses(text):
    """เพิ่มจังหวะหยุดให้เหมือนคนพูด"""
    # หลัง hook ให้หยุดยาว
    text = text.replace("?", "?...")
    text = text.replace("รู้หรือไม่?", "รู้หรือไม่?...")
    # หลังเลขข้อ ให้หยุดสั้น
    text = re.sub(r"ข้อ(\d)", r"ข้อ \1...", text)
    text = re.sub(r"(\d+)\.", r"\1... ", text)
    # หลังคำเชื่อม ให้หยุด
    for w in ["เพราะว่า", "แต่", "สรุปคือ", "จริงๆ แล้ว"]:
        text = text.replace(w, f"...{w}")
    # เพิ่ม ... ระหว่างประโยคให้มีจังหวะ
    text = text.replace("。", "... ")
    text = text.replace("!", "!... ")
    return text

def build_ssml(script_data, voice="th-TH-NiwatNeural"):
    """
    สร้าง SSML ที่มีอารมณ์
    Hook = ตื่นเต้น, Point1 = เล่า, Point2 = เน้น, Point3 = เฉลย, CTA = ชวนคุย
    """
    hook = script_data.get("hook", "รู้หรือไม่?")
    p1 = script_data.get("point1", "")
    p2 = script_data.get("point2", "")
    p3 = script_data.get("point3", "")
    cta = script_data.get("cta", "")
    
    # เพิ่มจังหวะ
    hook = add_drama_pauses(hook)
    p1 = add_drama_pauses(p1)
    p2 = add_drama_pauses(p2)
    p3 = add_drama_pauses(p3)
    cta = add_drama_pauses(cta)

    # สร้าง SSML
    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
<voice name="{voice}">
"""

    # Hook - ตื่นเต้น
    ssml += f'  <prosody rate="{EMOTION_SSML["hook"]["rate"]}" pitch="{EMOTION_SSML["hook"]["pitch"]}">\n'
    ssml += f'    {hook}\n'
    ssml += f'  </prosody>\n'
    ssml += f'  <break time="600ms"/>\n'

    # Point 1 - ปกติ
    ssml += f'  <prosody rate="{EMOTION_SSML["point1"]["rate"]}" pitch="{EMOTION_SSML["point1"]["pitch"]}">\n'
    ssml += f'    ข้อหนึ่ง... {p1}\n'
    ssml += f'  </prosody>\n'
    ssml += f'  <break time="400ms"/>\n'

    # Point 2 - เน้น
    ssml += f'  <prosody rate="{EMOTION_SSML["point2"]["rate"]}" pitch="{EMOTION_SSML["point2"]["pitch"]}">\n'
    ssml += f'    ข้อสอง... {p2}\n'
    ssml += f'  </prosody>\n'
    ssml += f'  <break time="400ms"/>\n'

    # Point 3 - เฉลยดีใจ
    ssml += f'  <prosody rate="{EMOTION_SSML["point3"]["rate"]}" pitch="{EMOTION_SSML["point3"]["pitch"]}">\n'
    ssml += f'    และข้อสาม... {p3}\n'
    ssml += f'  </prosody>\n'
    ssml += f'  <break time="500ms"/>\n'

    # CTA - ชวนคุย
    ssml += f'  <prosody rate="{EMOTION_SSML["cta"]["rate"]}" pitch="{EMOTION_SSML["cta"]["pitch"]}">\n'
    ssml += f'    {cta}\n'
    ssml += f'  </prosody>\n'

    ssml += f"</voice>\n</speak>"
    return ssml

def build_simple_ssml(full_script, voice="th-TH-NiwatNeural"):
    """แบบง่ายสำหรับ full_script เดียว"""
    text = add_drama_pauses(full_script)
    # แยกประโยค
    sentences = re.split(r'[.!?]+', text)
    ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH"><voice name="{voice}">\n'
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if not sent:
            continue
        if i == 0:
            # ประโยคแรกตื่นเต้น
            ssml += f'<prosody rate="+7%" pitch="+5%">{sent}.</prosody><break time="500ms"/>\n'
        elif i == len(sentences)-1:
            # ประโยคสุดท้ายชวนคุย
            ssml += f'<prosody rate="-1%" pitch="+1%">{sent}.</prosody>\n'
        else:
            ssml += f'{sent}.<break time="350ms"/>\n'
    ssml += '</voice></speak>'
    return ssml

async def _async_ssml(ssml_text, output_path, voice="th-TH-NiwatNeural"):
    communicate = edge_tts.Communicate(ssml_text, voice)
    await communicate.save(output_path)

def generate_human_voice(script_data, output_path, voice="th-TH-NiwatNeural", use_ssml=True):
    """
    สร้างเสียงเหมือนคนจริง
    script_data: dict มี hook, point1, point2, point3, cta, full_script
    """
    if not EDGE_AVAILABLE:
        print("[HumanTTS] edge-tts not installed")
        return False, None

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    if os.path.exists(output_path):
        try: os.remove(output_path)
        except: pass

    try:
        if use_ssml and "point1" in script_data:
            ssml = build_ssml(script_data, voice)
            # print(f"[HumanTTS] SSML:\n{ssml[:500]}")
        else:
            full = script_data.get("full_script", "")
            ssml = build_simple_ssml(full, voice)
        
        # edge-tts ต้องการให้ส่ง SSML แบบพิเศษ: ถ้าขึ้นต้นด้วย <speak> จะตีความเป็น SSML อัตโนมัติ
        asyncio.run(_async_ssml(ssml, output_path, voice))
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            dur = get_duration(output_path)
            print(f"[HumanTTS] ✅ {voice} มีอารมณ์ {dur:.1f}s" if dur else f"[HumanTTS] ✅ {voice}")
            return True, dur
        return False, None
    except Exception as e:
        print(f"[HumanTTS] ❌ {e}")
        import traceback; traceback.print_exc()
        return False, None

def generate_simple_human(full_script, output_path, voice="th-TH-NiwatNeural"):
    """ใช้ง่าย: ส่ง full_script อย่างเดียว"""
    return generate_human_voice({"full_script": full_script}, output_path, voice, use_ssml=False)

def get_duration(path):
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
            return None

# ElevenLabs (ถ้ามี API key จะเสียงดีกว่า)
def generate_elevenlabs(text, output_path, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """พรีเมี่ยม: ElevenLabs เสียงเหมือนคน 100% - ต้องมี API key"""
    if not api_key:
        print("[ElevenLabs] No API key")
        return False, None
    try:
        import requests
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.4}
        }
        resp = requests.post(url, json=data, headers=headers, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            if os.path.getsize(output_path) > 1000:
                dur = get_duration(output_path)
                print(f"[ElevenLabs] ✅ {dur:.1f}s" if dur else "[ElevenLabs] ✅")
                return True, dur
        else:
            print(f"[ElevenLabs] ❌ {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[ElevenLabs] ❌ {e}")
    return False, None

def generate_best_voice(script_data, output_path, settings=None):
    """
    เลือกเสียงที่ดีที่สุดตาม settings
    ลำดับ: ElevenLabs (ถ้ามี key) -> edge-tts SSML (ฟรี, ดีมาก)
    """
    settings = settings or {}
    eleven_key = settings.get("elevenlabs_key", "") or settings.get("tts", {}).get("elevenlabs_key", "")
    
    # ลอง ElevenLabs ก่อนถ้ามี
    if eleven_key:
        full = script_data.get("full_script", "")
        ok, dur = generate_elevenlabs(full, output_path, eleven_key)
        if ok:
            return True, dur
    
    # ใช้ edge-tts SSML (ฟรีแต่ดีมาก)
    voice = settings.get("tts", {}).get("voice", "th-TH-NiwatNeural") if isinstance(settings.get("tts"), dict) else settings.get("voice", "th-TH-NiwatNeural")
    return generate_human_voice(script_data, output_path, voice, use_ssml=True)
