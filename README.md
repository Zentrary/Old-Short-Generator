# Content Generator + Auto Knowledge Factory

เครื่องมือสร้างคลิป Shorts แบบเก่า (Quotes) + โรงงานใหม่ **"รู้หรือไม่ใน 1 นาที"** อัตโนมัติ 100%

## โครงสร้างใหม่

- `main.py` - แอปเดิม (CustomTkinter) สำหรับคลิปคำคม/แรงบันดาลใจ
- `auto_factory.py` ⭐ - โรงงานอัตโนมัติสำหรับช่องความรู้ 1 นาที (ไม่มี GUI รันได้เอง)
- `factory/` - 9 โมดูลโรงงาน
- `config/knowledge.json` - 4 เสาหลัก 40 หัวข้อพร้อมใช้
- `config/factory_settings.json` - ตั้งค่าโรงงานทั้งหมด
- `docs/SYSTEM_DESIGN.md` - เอกสารวางระบบละเอียด (ภาษาไทย)

## Auto Knowledge Factory - ทำอะไรได้บ้าง?

```
[หาเรื่อง] → [เขียนบทด้วย Groq] → [พากย์ไทย] → [หาคลิปพื้นหลัง] → [ตัดต่อ+ซับไทย] → [ตั้งชื่อ/คำอธิบาย/แท็ก] → [ตั้งเวลาลง] → [วิเคราะห์ย้อนกลับ]
```

* **ไม่ต้องกดอะไรเลย** - ตั้ง Task Scheduler ให้รัน `python auto_factory.py --daily --batch 2` ทุกเช้าตี 5
* **ไม่ซ้ำหัวข้อ** - จำ `used_topics` ใน `outputs/logs/history.json`
* **มี Fallback** - ถ้า Groq/เน็ตล่ม ใช้ Template สำรอง ไม่ให้โรงงานหยุด
* **กันไฟล์เสีย** - ตรวจความยาวคลิปก่อนส่ง
* **ใช้ของเดิมได้** - ใช้ `settings.json` เดิม (Groq/Pexels/Pixabay keys เดิม)

## 4 เสาหลัก (วนตามวัน)

| วัน | หมวด | ตัวอย่างหัวข้อ |
|-----|------|---------------|
| จันทร์, พฤหัส | 🧠 จิตวิทยา | ทำไมคนฉลาดถึงมีเพื่อนน้อย |
| อังคาร, ศุกร์ | 💰 เงิน | ทำไมคนรวยไม่เก็บเงินในธนาคาร |
| พุธ, เสาร์ | 🏥 สุขภาพ | ทำไมนอน 8 ชม. ยังง่วง |
| อาทิตย์ | 🏛️ ประวัติศาสตร์ | ทำไมปิรามิดสร้างตรงกันทั่วโลก |

หัวข้อเริ่มต้น 40 อันใน `config/knowledge.json` เติมเองได้

## ติดตั้ง

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-factory.txt  # หรือ requirements เดิม
# หรือ
.venv/bin/pip install moviepy pillow numpy groq edge_tts requests cloudscraper

# สร้าง placeholder สำหรับทดสอบ (ถ้ายังไม่มีวิดีโอ)
.venv/bin/python tools/generate_placeholders.py

# โหลดฟอนต์ไทย NotoSansThai (ถ้ายังไม่มี)
curl -L -o assets/fonts/NotoSansThai-Black.ttf https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai-Black.ttf
```

## วิธีใช้โรงงาน

```bash
# ทดสอบ 1 คลิป (ไม่เรนเดอร์จริง)
.venv/bin/python auto_factory.py --once --dry-run

# ทดสอบ 1 คลิปจริง (10-15 วิ)
.venv/bin/python auto_factory.py --once --pillar Psychology

# กำหนดหัวข้อเอง
.venv/bin/python auto_factory.py --once --topic "ทำไมเราถึงฝัน" --pillar Psychology

# รันรายวัน 2 คลิป + ตั้งเวลาลง 07:30/19:30
.venv/bin/python auto_factory.py --daily --batch 2

# รันพร้อมอัพโหลด YouTube (ต้องมี credentials)
.venv/bin/python auto_factory.py --daily --batch 2 --upload

# ตรวจวัตถุดิบ
.venv/bin/python auto_factory.py --check-assets

# ดูหัวข้อทั้งหมด
.venv/bin/python auto_factory.py --list-topics

# ดูรายงาน
.venv/bin/python -m factory.analytics
```

## ตั้งค่าโรงงาน (`config/factory_settings.json`)

```json
{
  "video": {"duration": 60, "volume": 0.4, "filter": "Darken (Cinematic)"},
  "tts": {"enabled": true, "voice": "th-TH-NiwatNeural"},
  "generation": {"schedule_times": ["07:30", "19:30"], "auto_upload": false},
  "channel": {"branding_text": "รู้หรือไม่? 1นาทีรู้เรื่อง"}
}
```

* `duration`: 60 = 1 นาทีเต็ม, 10-15 = สำหรับทดสอบเร็ว
* `tts.enabled`: true = พากย์ไทย (ต้องต่อเน็ตได้), false = ใช้แค่เพลง+ซับ
* `schedule_times`: เวลาลง (ตั้ง Task Scheduler ให้ตรง)

## ตั้งรันอัตโนมัติ (Windows Task Scheduler)

1. เปิด Task Scheduler → Create Task
2. Trigger: Daily 05:00
3. Action: `C:\path\to\.venv\Scripts\python.exe auto_factory.py --daily --batch 2`
4. Start in: `C:\path\to\Old-Short-Generator`

## โครงสร้างไฟล์

```
config/
  settings.json              # API keys เดิม
  knowledge.json             # 4 เสาหลัก + 40 หัวข้อ
  factory_settings.json      # ตั้งค่าโรงงาน
  schedule.json              # ตารางลง (แชร์กับ main.py)
factory/
  knowledge.py               # สมองหาเรื่อง
  script_engine.py            # เขียนบทด้วย Groq
  tts_engine.py              # พากย์ไทย
  media_engine.py            # หาคลิป Pexels/Pixabay
  renderer.py                # ตัดต่อ 1080x1920 + ซับไทย
  metadata_engine.py         # ชื่อ/คำอธิบาย/แท็ก
  scheduler.py               # ตั้งเวลา
  uploader.py                # อัพโหลด YouTube/Selenium
  analytics.py               # รายงาน
outputs/
  knowledge/                 # วิดีโอเสร็จ
  logs/history.json          # กันซ้ำ + ประวัติ
docs/SYSTEM_DESIGN.md        # เอกสารวางระบบ
```

## สูตรคลิป 60 วิ

- 0-3วิ: Hook "รู้หรือไม่? + คำถามแรง"
- 3-48วิ: 3 ข้อ (ข้อละ 12-15วิ)
- 48-57วิ: สรุป 1 ประโยค
- 57-60วิ: CTA "คอมเมนต์เลข 1/2"

## ทดสอบสำเร็จ

```
outputs/knowledge/
  20261018_064638_History_beb73f.mp4 (1013K, 10s, 1080x1920)
  20261018_064738_History_eb01a1.mp4 (1013K, 10s, 1080x1920)
outputs/logs/history.json
  used_topics: 2 รายการ
  generated: 2 รายการ
config/schedule.json
  2026-10-18 07:30 / 19:30 pending
```

## FAQ

**Q: ไม่มี Groq key?**
A: โรงงานมี Fallback Template ไม่ต้องมี key ก็รันได้ แต่บทจะสั้นกว่า

**Q: อยากใช้ TTS ไทย?**
A: เปิด `tts.enabled: true` และต้องต่อเน็ตได้ (speech.platform.bing.com ต้องเข้าถึงได้) ถ้า offline จะใช้แค่เพลง

**Q: วิดีโอไม่มี?**
A: รัน `tools/generate_placeholders.py` หรือวาง .mp4 ลง `assets/backgrounds/Knowledge_*/`

**Q: จะกลับไปใช้ main.py เดิมได้ไหม?**
A: ได้เลย ไม่ได้แก้ main.py สักบรรทัด

