"""
script_engine.py - เขียนบท 60วิ อัตโนมัติ
ใช้ Groq + Fallback Template
"""
import json
import re
import random

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except:
    GROQ_AVAILABLE = False

# Template สำรอง ถ้า Groq ล่ม
FALLBACK_TEMPLATES = {
    "Psychology": [
        {
            "hook": "รู้หรือไม่? ทำไม{topic_short}?",
            "body": "ข้อ1: สมองเรามีระบบจดจำเรื่องแย่แรงกว่าดี 5 เท่า เพื่อเอาตัวรอด\nข้อ2: พอมันจำเรื่องแย่ มันจะวนคิดซ้ำๆ ทำให้เราฝังใจ\nข้อ3: วิธีแก้คือ ก่อนนอนเขียน 3 เรื่องดีๆ สมองจะเริ่มจำด้านดีเก่งขึ้น",
            "cta": "แล้วคุณล่ะ เป็นแบบนี้ไหม? คอมเมนต์เลข 1 ถ้าใช่ เลข 2 ถ้าไม่เคย"
        }
    ],
    "Money": [
        {
            "hook": "รู้หรือไม่? ทำไม{topic_short}?",
            "body": "ข้อ1: เงินเฟ้อปีละ 3% ฝากธนาคารดอก 1% เท่ากับขาดทุน\nข้อ2: คนรวยเลยไม่ปล่อยเงินนอนนิ่ง แต่ให้เงินทำงานต่อ\nข้อ3: เริ่มง่ายๆ แค่ออมวันละ 50 บาทในกองทุน ก็ชนะเงินเฟ้อแล้ว",
            "cta": "คุณเก็บเงินแบบไหนอยู่? คอมเมนต์ 1=ฝากธนาคาร 2=ลงทุน"
        }
    ],
    "Health": [
        {
            "hook": "รู้หรือไม่? {topic}ช่วยอะไร?",
            "body": "ข้อ1: กระตุ้นสมองให้ตื่นเร็วกว่ากาแฟ\nข้อ2: ล้างของเสียที่ไตกรองมาทั้งคืน\nข้อ3: ทำให้ระบบขับถ่ายทำงานตรงเวลา",
            "cta": "คืนนี้ลองทำดู แล้วพรุ่งนี้คุณจะรู้สึกต่างเลย คอมเมนต์บอกผลด้วยนะ"
        }
    ],
    "History": [
        {
            "hook": "รู้หรือไม่? ทำไม{topic_short}?",
            "body": "ข้อ1: นักวิทยาศาสตร์พบหลักฐานใหม่ที่เปลี่ยนความเชื่อเดิม\nข้อ2: มันเกี่ยวข้องกับสิ่งที่เราทำทุกวันโดยไม่รู้ตัว\nข้อ3: และมันอธิบายว่าทำไมโลกเราถึงเป็นแบบทุกวันนี้",
            "cta": "คุณเคยสงสัยเรื่องนี้ไหม? คอมเมนต์เลข 1 ถ้าเคย"
        }
    ]
}

BRANCH_PROMPTS = {
    "Psychology": "จิตวิทยา พฤติกรรมมนุษย์ สมอง ความสัมพันธ์",
    "Money": "การเงิน ลงทุน เก็บเงิน ความมั่งคั่ง",
    "Health": "สุขภาพ การนอน อาหาร การออกกำลังกาย สมอง",
    "History": "ประวัติศาสตร์ วิทยาศาสตร์ อวกาศ ธรรมชาติ สิ่งมหัศจรรย์"
}

def build_prompt(topic, pillar):
    branch_desc = BRANCH_PROMPTS.get(pillar, pillar)
    prompt = f"""คุณคือนักเขียนสคริปต์ "รู้หรือไม่ใน 1 นาที" ภาษาไทย

หัวข้อ: "{topic}"
หมวด: {pillar} ({branch_desc})

จงเขียนสคริปต์วิดีโอ 60 วินาที ภาษาไทยเข้าใจง่าย คนอายุ 18-35 ฟังแล้วเข้าใจทันที

กฎเข้ม:
1. เปิดด้วย hook คำถามชวนสงสัย 1 ประโยค ไม่เกิน 15 คำ ต้องมีคำว่า "รู้หรือไม่?" และชวนให้ดูต่อ
2. เนื้อหาแบ่งเป็น 3 ข้อสั้นๆ แต่ละข้อ 1-2 ประโยค อธิบายด้วยเหตุผลวิทยาศาสตร์/จิตวิทยา/ประวัติศาสตร์ (ใช้ "นักวิจัยพบว่า" ถ้าไม่แน่ใจ)
3. ปิดด้วยสรุป 1 ประโยค + คำถามชวนคอมเมนต์ (เช่น "คอมเมนต์เลข 1 ถ้า... เลข 2 ถ้า...")
4. ทั้งหมดอ่านออกเสียงแล้วต้องยาว 55-60 วินาที (ประมาณ 130-150 คำไทย)
5. ห้ามมั่วข้อมูลร้ายแรง ห้ามให้คำแนะนำการแพทย์/การเงินที่เสี่ยง
6. ส่งกลับเป็น JSON เท่านั้น ห้ามมีข้อความอื่น:
{{"hook": "...", "point1": "...", "point2": "...", "point3": "...", "summary": "...", "cta": "...", "full_script": "...", "title": "ชื่อคลิปสั้นไม่เกิน 60 ตัวอักษร"}}

ตัวอย่าง full_script: "รู้หรือไม่? ทำไมเราถึงจำคำด่าได้แม่นกว่าคำชม? เพราะสมองมีระบบ Negativity Bias มันจะจำเรื่องแย่แรงกว่าดี 5 เท่า เพื่อเอาตัวรอด ข้อหนึ่ง... ข้อสอง... ข้อสาม... สรุปคือ... แล้วคุณล่ะ เป็นแบบไหน คอมเมนต์บอกหน่อย"

เริ่มเลย:"""
    return prompt

def call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    if not GROQ_AVAILABLE or not api_key:
        return None
    
    try:
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.85,
            max_tokens=800
        )
        content = chat.choices[0].message.content.strip()
        # ลองหา JSON ในข้อความ
        # หา { ... } ก้อนแรก
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"[ScriptEngine] Groq error: {e}")
        return None

def fallback_script(topic, pillar):
    """สร้างสคริปต์จาก template ถ้า Groq ล่ม"""
    templates = FALLBACK_TEMPLATES.get(pillar, FALLBACK_TEMPLATES["Psychology"])
    t = random.choice(templates)
    
    # เติม topic
    topic_short = topic.replace("ทำไม", "").replace("?", "").strip()[:20]
    hook = t["hook"].format(topic_short=topic_short, topic=topic)
    body = t["body"]
    cta = t["cta"]
    
    # แยก body เป็น point1,2,3
    points = body.split("\n")
    point1 = points[0].replace("ข้อ1:", "").strip() if len(points) > 0 else "นักวิจัยพบว่ามันเกี่ยวกับสมอง"
    point2 = points[1].replace("ข้อ2:", "").strip() if len(points) > 1 else "มันส่งผลต่อชีวิตประจำวันของเรา"
    point3 = points[2].replace("ข้อ3:", "").strip() if len(points) > 2 else "วิธีแก้ง่ายๆ คือเริ่มทำวันนี้"
    
    full_script = f"{hook} {point1} {point2} {point3} สรุปคือ {topic} มีเหตุผลทางวิทยาศาสตร์รองรับ {cta}"
    
    # สร้าง title
    title = f"{topic} | {pillar} 1 นาที"
    if len(title) > 60:
        title = topic[:50] + "..."
    
    return {
        "hook": hook,
        "point1": point1,
        "point2": point2,
        "point3": point3,
        "summary": f"สรุปคือ {topic} มีเหตุผลทางวิทยาศาสตร์",
        "cta": cta,
        "full_script": full_script,
        "title": title
    }

def validate_script(data, topic, pillar):
    """ตรวจว่าสคริปต์ครบไหม"""
    required = ["hook", "full_script", "title"]
    for r in required:
        if r not in data or not str(data[r]).strip():
            print(f"[ScriptEngine] Missing {r} in data: {data}")
            return False
    
    # ถ้าไม่มี point1-3 ให้แยกจาก full_script
    if "point1" not in data:
        data["point1"] = data["full_script"][:80]
    if "point2" not in data:
        data["point2"] = data["full_script"][80:160]
    if "point3" not in data:
        data["point3"] = data["full_script"][160:240]
    if "cta" not in data:
        data["cta"] = "คุณคิดยังไง คอมเมนต์บอกหน่อย"
    if "summary" not in data:
        data["summary"] = "นี่คือเหตุผลที่คุณควรรู้"
    
    # ตรวจความยาว full_script คร่าวๆ
    wc = len(data["full_script"])
    if wc < 50:
        data["full_script"] += " " + data["cta"]
    if wc > 1000:
        data["full_script"] = data["full_script"][:900] + " " + data["cta"]
    
    return True

def write_script(topic, pillar, groq_key=None, model="llama-3.3-70b-versatile"):
    """
    เขียนสคริปต์ 1 เรื่อง
    return: dict {hook, point1, point2, point3, summary, cta, full_script, title, pillar, topic}
    """
    prompt = build_prompt(topic, pillar)
    data = call_groq(prompt, groq_key, model) if groq_key else None
    
    if data and validate_script(data, topic, pillar):
        data["pillar"] = pillar
        data["topic"] = topic
        data["source"] = "groq"
        print(f"[ScriptEngine] ✅ Groq generated: {data['title'][:50]}")
        return data
    else:
        print(f"[ScriptEngine] ⚠️ Fallback template for: {topic}")
        data = fallback_script(topic, pillar)
        data["pillar"] = pillar
        data["topic"] = topic
        data["source"] = "fallback"
        return data

def estimate_duration(full_script, wpm=160):
    """ประมาณความยาวเสียงพูด (คำไทย/นาที)"""
    # ไทยประมาณ 2.5 ตัวอักษร = 1 คำพูด
    chars = len(full_script)
    words = chars / 2.5
    minutes = words / wpm
    seconds = minutes * 60
    return seconds
