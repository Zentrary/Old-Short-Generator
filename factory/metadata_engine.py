"""
metadata_engine.py - สร้างชื่อคลิป คำอธิบาย แท็ก ปก
"""
import re

PILLAR_HASHTAGS = {
    "Psychology": ["#รู้หรือไม่", "#จิตวิทยา", "#จิตวิทยา1นาที", "#ความรู้", "#สมอง", "#shorts", "#พัฒนาตัวเอง"],
    "Money": ["#รู้หรือไม่", "#การเงิน", "#เก็บเงิน", "#ลงทุน", "#ความรู้การเงิน", "#shorts", "#หาเงิน"],
    "Health": ["#รู้หรือไม่", "#สุขภาพ", "#สุขภาพดี", "#ความรู้สุขภาพ", "#เคล็ดลับสุขภาพ", "#shorts"],
    "History": ["#รู้หรือไม่", "#ประวัติศาสตร์", "#วิทยาศาสตร์", "#ความรู้รอบตัว", "#สาระ", "#shorts"]
}

PILLAR_EMOJI = {
    "Psychology": "🧠",
    "Money": "💰",
    "Health": "🏥",
    "History": "🏛️"
}

def build_title(script_data, pillar):
    """
    สร้างชื่อคลิปตามสูตร: [Hook] | [หมวด] 1 นาที
    ต้องไม่เกิน 100 ตัวอักษร (YouTube ตัด)
    """
    hook = script_data.get("hook", "").strip()
    title_from_ai = script_data.get("title", "").strip()
    
    # ถ้า AI ให้ title มาแล้วและสั้นพอ ใช้เลย
    if title_from_ai and len(title_from_ai) <= 100 and "รู้หรือไม่" not in title_from_ai.lower():
        # เติม hook ถ้ายังไม่มี
        title = title_from_ai
    else:
        # สร้างจาก hook
        # ลบ "รู้หรือไม่?" ออกจาก hook ถ้ามี แล้วเติมใหม่ให้สวย
        clean_hook = hook.replace("รู้หรือไม่?", "").replace("รู้หรือไม่", "").strip(" ?!。")
        if not clean_hook:
            clean_hook = script_data.get("topic", "เรื่องน่ารู้")
        title = f"{clean_hook} | {get_pillar_th(pillar)} 1 นาที"
    
    # ถ้ายาวไป ตัด
    if len(title) > 95:
        title = title[:92] + "..."
    
    return title

def get_pillar_th(pillar):
    mapping = {
        "Psychology": "จิตวิทยา",
        "Money": "การเงิน",
        "Health": "สุขภาพ",
        "History": "ประวัติศาสตร์"
    }
    return mapping.get(pillar, pillar)

def build_description(script_data, pillar):
    """
    สร้างคำอธิบายคลิป
    """
    hook = script_data.get("hook", "")
    p1 = script_data.get("point1", "")
    p2 = script_data.get("point2", "")
    p3 = script_data.get("point3", "")
    cta = script_data.get("cta", "")
    topic = script_data.get("topic", "")
    
    pillar_th = get_pillar_th(pillar)
    emoji = PILLAR_EMOJI.get(pillar, "📌")
    
    desc = f"""{hook}

{emoji} สรุปในคลิปนี้:
1️⃣ {p1}
2️⃣ {p2}
3️⃣ {p3}

💡 สรุป: {script_data.get('summary', '')}

{cta}

━━━━━━━━━━━━━━━
🎬 ช่อง "รู้หรือไม่ใน 1 นาที"
1 คลิป 1 ความรู้ ดูก่อนนอนฉลาดขึ้นวันละนิด
กดติดตามไว้ ไม่พลาดความรู้ใหม่ทุกวัน 👇

#รู้หรือไม่ #ความรู้1นาที #{pillar_th} #shorts #สาระ
"""
    return desc.strip()

def build_tags(pillar, topic, script_data=None):
    """สร้างแท็ก YouTube"""
    base = PILLAR_HASHTAGS.get(pillar, ["#รู้หรือไม่", "#shorts"])
    # เติมคำจาก topic
    topic_tags = []
    # แยกคำไทยจาก topic
    words = re.findall(r'[ก-ฮa-zA-Z]+', topic)
    for w in words[:3]:
        if len(w) >= 2:
            topic_tags.append(f"#{w}")
    
    all_tags = base + topic_tags
    
    # ทำเป็น string คั่นด้วย comma สำหรับ YouTube API
    # และแบบ list สำหรับเก็บใน JSON
    return all_tags

def build_thumbnail_text(script_data, pillar):
    """ข้อความสั้นๆ สำหรับใส่บนปก (3-4 คำ)"""
    topic = script_data.get("topic", "")
    # ดึงคำสำคัญ
    # เช่น "ทำไมคนฉลาดถึงมีเพื่อนน้อย" → "ฉลาด = เหงา?"
    topic_short = topic.replace("ทำไม", "").replace("?", "").replace("ถึง", " ").strip()
    words = topic_short.split()
    if len(words) >= 3:
        thumb = " ".join(words[:3]) + "?"
    else:
        thumb = topic_short[:12] + "?"
    
    return thumb

def build_all_metadata(script_data, pillar):
    """สร้าง metadata ครบชุด"""
    title = build_title(script_data, pillar)
    description = build_description(script_data, pillar)
    tags = build_tags(pillar, script_data.get("topic", ""), script_data)
    thumb_text = build_thumbnail_text(script_data, pillar)
    
    return {
        "title": title,
        "description": description,
        "tags": tags,
        "thumb_text": thumb_text,
        "pillar": pillar,
        "pillar_th": get_pillar_th(pillar),
        "emoji": PILLAR_EMOJI.get(pillar, "📌")
    }
