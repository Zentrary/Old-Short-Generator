"""
analytics.py - วิเคราะห์ย้อนกลับ (เฟส 2)
ดึงยอดวิวจาก YouTube Studio หรือไฟล์ log
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

def load_history():
    try:
        with open("outputs/logs/history.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("generated", [])
            return data
    except:
        return []

def load_schedule():
    try:
        with open("config/schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_social_history():
    try:
        with open("config/social_history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def generate_report():
    """
    สร้างรายงานสรุป
    """
    history = load_history()
    schedule = load_schedule()
    social = load_social_history()
    
    print("\n" + "="*60)
    print("📊 รายงานโรงงานรู้หรือไม่")
    print("="*60)
    
    # นับตาม pillar
    pillar_count = defaultdict(int)
    for h in history:
        pillar_count[h.get("theme", "Unknown")] += 1
    
    print("\n📌 ผลิตไปแล้ว:")
    for pillar, count in pillar_count.items():
        print(f"   {pillar}: {count} คลิป")
    print(f"   รวม: {len(history)} คลิป")
    
    # ตารางที่รอลง
    pending = 0
    posted = 0
    for date, slots in schedule.items():
        for s in slots:
            if s.get("status") == "pending":
                pending += 1
            elif s.get("status") == "posted":
                posted += 1
    
    print(f"\n📅 ตารางลง:")
    print(f"   รอลง: {pending} คลิป")
    print(f"   ลงแล้ว: {posted} คลิป")
    
    # อัพโหลด
    success = sum(1 for s in social if s.get("status") == "Success")
    failed = sum(1 for s in social if s.get("status") != "Success")
    print(f"\n📤 อัพโหลด:")
    print(f"   สำเร็จ: {success}")
    print(f"   ล้มเหลว: {failed}")
    
    # แนะนำ
    print(f"\n💡 คำแนะนำ:")
    if not history:
        print("   → ยังไม่เคยผลิต ลองรัน python auto_factory.py --once")
    elif pending == 0:
        print("   → ตารางว่าง! รัน python auto_factory.py --daily --batch 2 เพื่อเติม")
    elif pillar_count:
        most = max(pillar_count, key=lambda k: pillar_count[k])
        least = min(pillar_count, key=lambda k: pillar_count[k])
        print(f"   → ทำ {most} เยอะสุด ({pillar_count[most]} คลิป) ลองเพิ่ม {least} บ้างเพื่อความหลากหลาย")
    
    print("="*60 + "\n")
    
    return {
        "total_produced": len(history),
        "by_pillar": dict(pillar_count),
        "pending": pending,
        "posted": posted,
        "upload_success": success
    }

if __name__ == "__main__":
    generate_report()
