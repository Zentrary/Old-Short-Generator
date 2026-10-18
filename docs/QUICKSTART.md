# 🚀 Quickstart - เริ่มโรงงานใน 5 นาที

## ขั้น 1: เตรียมวัตถุดิบ (1 นาที)

```bash
python -m venv .venv
.venv/bin/pip install moviepy pillow numpy groq edge_tts requests cloudscraper
.venv/bin/python tools/generate_placeholders.py
```

ถ้ายังไม่มีฟอนต์ไทย:
```bash
curl -L -o assets/fonts/NotoSansThai-Black.ttf https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai-Black.ttf
```

## ขั้น 2: ทดสอบ 1 คลิป (2 นาที)

```bash
.venv/bin/python auto_factory.py --once --dry-run    # ดูบทก่อน
.venv/bin/python auto_factory.py --once --pillar Money  # เรนเดอร์จริง 10วิ
ls outputs/knowledge/
```

ถ้าได้ไฟล์ .mp4 1080x1920 = สำเร็จ

## ขั้น 3: ตั้งค่าเสียง (30 วิ)

เปิด `config/factory_settings.json`:
- `tts.enabled: false` = ใช้แค่เพลง (offline ได้)
- `tts.enabled: true`  = พากย์ไทยด้วย (ต้องต่อเน็ต)

## ขั้น 4: รันรายวัน (1 นาที)

```bash
.venv/bin/python auto_factory.py --daily --batch 2
cat outputs/logs/history.json
cat config/schedule.json
```

ได้ 2 คลิป + ตารางลง 07:30/19:30 อัตโนมัติ

## ขั้น 5: ตั้งให้รันเองทุกเช้า

**Windows:**
Task Scheduler → Daily 05:00 → `.\.venv\Scripts\python.exe auto_factory.py --daily --batch 2`

**Linux/Mac:**
```bash
crontab -e
# เพิ่มบรรทัดนี้
0 5 * * * cd /path/to/Old-Short-Generator && .venv/bin/python auto_factory.py --daily --batch 2
```

---

## ดูหัวข้อทั้งหมด

```bash
.venv/bin/python auto_factory.py --list-topics
```

## เพิ่มหัวข้อเอง

แก้ไข `config/knowledge.json`:

```json
"Psychology": [
  "ทำไมเราถึง...",
  "หัวข้อใหม่ของคุณ"
]
```

## เปลี่ยนเวลาลง

ใน `config/factory_settings.json`:

```json
"schedule_times": ["07:30", "12:00", "19:30"]
```

## เปิดโหมด 60วิเต็ม (Production)

```json
"video": {"duration": 60}
```

*ทดสอบใช้ 10วิ เร็วกว่า 6 เท่า*

---

จบ! โรงงานพร้อมผลิตแล้ว 🎉
