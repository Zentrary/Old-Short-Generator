"""
knowledge.py - สมองหาเรื่อง (Topic Brain)
เลือกหัวข้อตามวัน ไม่ให้ซ้ำ
"""
import json
import os
import random
from datetime import datetime
from factory.config import load_json, save_json

HISTORY_PATH = "outputs/logs/history.json"
KNOWLEDGE_PATH = "config/knowledge.json"

WEEKDAY_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

def load_knowledge():
    return load_json(KNOWLEDGE_PATH, {})

def load_history():
    data = load_json(HISTORY_PATH, None)
    if data is None:
        return {"used_topics": [], "generated": []}
    # รองรับ format เก่า
    if isinstance(data, list):
        return {"used_topics": [], "generated": data}
    if "used_topics" not in data:
        data["used_topics"] = []
    if "generated" not in data:
        data["generated"] = []
    return data

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    save_json(HISTORY_PATH, history)

def get_pillar_for_today(knowledge=None, date=None):
    """เลือกเสาหลักตามวัน"""
    if knowledge is None:
        knowledge = load_knowledge()
    if date is None:
        date = datetime.now()
    
    weekday = WEEKDAY_MAP[date.weekday()]
    template = knowledge.get("schedule_template", {})
    pillar = template.get(weekday, "Psychology")
    return pillar

def pick_topic(pillar=None, date=None, knowledge=None, history=None):
    """
    เลือกหัวข้อที่ไม่ซ้ำ
    return: (pillar, topic)
    """
    if knowledge is None:
        knowledge = load_knowledge()
    if history is None:
        history = load_history()
    
    if pillar is None:
        pillar = get_pillar_for_today(knowledge, date)
    
    topics = knowledge.get("topics", {}).get(pillar, [])
    if not topics:
        # fallback สุ่มจากทุก pillar
        all_topics = []
        for p, tlist in knowledge.get("topics", {}).items():
            for t in tlist:
                all_topics.append((p, t))
        # กรองที่ยังไม่เคยใช้
        used = set(history.get("used_topics", []))
        candidates = [x for x in all_topics if x[1] not in used]
        if not candidates:
            candidates = all_topics
            # รีเซ็ตถ้าใช้หมดแล้ว
            history["used_topics"] = []
            save_history(history)
        return random.choice(candidates) if candidates else (pillar, "ทำไมเราถึงฝัน")
    
    used = set(history.get("used_topics", []))
    candidates = [t for t in topics if t not in used]
    
    if not candidates:
        # ใช้หมดแล้ว รีเซ็ต
        candidates = topics
        # ลบของ pillar นี้ออกจาก used เพื่อให้วนใหม่ได้
        history["used_topics"] = [x for x in used if x not in topics]
        save_history(history)
    
    topic = random.choice(candidates)
    return pillar, topic

def mark_topic_used(topic, history=None):
    """บันทึกว่าใช้หัวข้อนี้แล้ว"""
    if history is None:
        history = load_history()
    if topic not in history.get("used_topics", []):
        if "used_topics" not in history:
            history["used_topics"] = []
        history["used_topics"].append(topic)
        save_history(history)
    return history

def get_pillar_info(pillar, knowledge=None):
    if knowledge is None:
        knowledge = load_knowledge()
    return knowledge.get("pillars", {}).get(pillar, {})

def generate_new_topics_with_groq(pillar, groq_key, count=10):
    """
    ถ้าหัวข้อหมด ให้ Groq คิดใหม่ (เรียกจาก script_engine)
    Placeholder - เรียกจริงใน script_engine.py
    """
    pass
