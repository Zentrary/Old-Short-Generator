"""
scheduler.py - ตั้งเวลาลงอัตโนมัติ
Reuse ScheduleManager จาก main.py
"""
import os
import json
import random
from datetime import datetime, timedelta

SCHEDULE_PATH = "config/schedule.json"

def load_schedule():
    try:
        with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_schedule(data):
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_schedule(files, start_date=None, times_per_day=None):
    """
    สร้างตารางลง 30 วัน
    files: list ของชื่อไฟล์ใน outputs/knowledge
    times_per_day: เช่น ["07:30", "19:30"]
    """
    if start_date is None:
        start_date = datetime.now()
    if times_per_day is None:
        # โหลดจาก factory_settings
        try:
            with open("config/factory_settings.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                times_per_day = cfg.get("generation", {}).get("schedule_times", ["07:30", "19:30"])
        except:
            times_per_day = ["07:30", "19:30"]
    
    schedule = load_schedule()
    pool = list(files)
    random.shuffle(pool)
    
    current = start_date
    assigned = 0
    safety = 365
    days = 0
    
    while pool and days < safety:
        date_str = current.strftime("%Y-%m-%d")
        slots = []
        for t in times_per_day:
            if not pool:
                break
            f = pool.pop(0)
            slots.append({"time": t, "file": f, "status": "pending"})
            assigned += 1
        if slots:
            # ถ้าวันนั้นมีอยู่แล้ว ให้ append
            if date_str in schedule:
                # รวมกับของเดิม
                existing = schedule[date_str]
                # กันซ้ำ
                existing_files = {s["file"] for s in existing}
                for s in slots:
                    if s["file"] not in existing_files:
                        existing.append(s)
            else:
                schedule[date_str] = slots
        
        current += timedelta(days=1)
        days += 1
    
    save_schedule(schedule)
    print(f"[Scheduler] ✅ Scheduled {assigned} videos across {days} days, times={times_per_day}")
    return assigned

def get_today_pending():
    """ดูว่าวันนี้มีคิวลงกี่คลิป"""
    schedule = load_schedule()
    today = datetime.now().strftime("%Y-%m-%d")
    return schedule.get(today, [])

def mark_posted(date_str, filename, status="posted"):
    schedule = load_schedule()
    if date_str in schedule:
        for slot in schedule[date_str]:
            if slot["file"] == filename:
                slot["status"] = status
        save_schedule(schedule)
