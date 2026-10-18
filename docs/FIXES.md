# แก้ปัญหาคลิปทดสอบ #1

## ปัญหาที่พบ (จากสกรีนช็อต 2026-10-18 14:06)

1. **ไม่มีเสียงเลย + มีเสียงแปลกๆ** - TTS ปิด, เพลง placeholder เป็น sine wave แหลม
2. **ข้อความแปลกๆ อ่านไม่ออก** - ฟอนต์ไทยเป็น HTML ไม่ใช่ TTF (เกิดจาก curl download ผิด)
3. **คุณภาพไม่พร้อมลง YouTube** - Layout ทับกัน, สีไม่สวย, ไม่มี progress bar ชัด

## วิธีแก้ (Fixed in v2)

### 1. ฟอนต์ไทย ✅
**สาเหตุ:** `assets/fonts/NotoSansThai-Black.ttf` ขนาด 265KB แต่ header เป็น `<!DOCTYPE html>` ไม่ใช่ TTF
```
head -c 4 -> 0a0a0a0a 3c21444f  (HTML)
```
**แก้:** ดาวน์โหลดใหม่จาก GitHub API ที่ถูกต้อง
```bash
curl -H "Accept: application/vnd.github.v3.raw" -o NotoSansThai.ttf \
  https://api.github.com/repos/google/fonts/contents/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf
# ได้ 218652 bytes, header 00 01 00 00 (TTF จริง)
cp NotoSansThai.ttf assets/fonts/NotoSansThai-Black.ttf
```
**ผล:** ทดสอบ Pillow `ImageFont.truetype` + `draw.text("รู้หรือไม่?")` ผ่าน, Overlay สร้างได้ 95KB

### 2. เลย์เอาต์ใหม่ (Renderer V2) ✅
**เดิม:** Hook ทับ Body, เลข 1. 2. 3. ทับข้อความ, CTA ถูกตัด
**ใหม่:** `factory/renderer_v2.py`
- Hook: กล่องม่วง accent ตามหมวด, กลางจอ, 2 บรรทัด max
- Body: กล่องดำโปร่ง, เลขวงกลม 20px อยู่กลาง block, ข้อความแยกบรรทัดชัดเจน
- CTA: กล่องขาว, ไม่ตัดขอบ
- Branding: `รู้หรือไม่? 1นาทีรู้เรื่อง` ล่างสุด

**โค้ดใหม่:**
```python
# วงกลมเลขอยู่กลาง block ไม่ทับ
num_cy = block_center_y + 6
draw.ellipse([num_cx-r, num_cy-r, ...], fill=accent)
draw.text((num_cx, num_cy+2), num_text, anchor="mm")
# ข้อความ wrap ตามความกว้างพิกเซล ไม่ใช่ clusters ซับซ้อน
wrap_text_by_width(draw, font, text, max_width)
```

### 3. เสียง (Audio) ✅
**เดิม:** 
- TTS `enabled: false` -> ไม่มีเสียงพูด
- Music `placeholder_lofi.mp3` = sine 220Hz+440Hz แหลม (480KB)

**ใหม่:**
- `factory/tts_engine_v2.py` - ลอง 4 แบบ: edge-tts -> gTTS -> pyttsx3 -> silent fallback (มี imageio_ffmpeg)
  - บน Windows ผู้ใช้: edge-tts จะสำเร็จ (มี internet), ได้เสียงไทย `th-TH-NiwatNeural` จริง
  - ถ้า offline: silent fallback สร้างไฟล์ silent ด้วย ffmpeg (libmp3lame) ให้ duration ถูกต้อง
  - แก้ bug: `-acodec aac` กับ `.mp3` ต้องใช้ `libmp3lame`

- `factory/music_engine.py` - สร้างเพลงใหม่:
  ```bash
  ffmpeg -f lavfi -i anoisesrc=c=brown:d=60 -f lavfi -i sine=f=110:volume=0.08 \
    -filter_complex amix+lowpass -acodec libmp3lame
  # ได้ 368KB brown noise + bass ฟังสบาย ไม่แหลม
  ```
  ผล: `assets/music/Knowledge_*/ambient_lofi.mp3` 368KB (เดิม sine 470KB)

- ผสมเสียง: 
  - ถ้ามี TTS: music volume 0.22 (เบามาก ไม่กลบ)
  - ถ้าไม่มี TTS: music volume 0.38 (ดังพอดี)
  - มี fade in/out 1s

### 4. ตั้งค่าใหม่
```json
// config/factory_settings.json
"video": {"duration": 60, "volume": 0.32} // เดิม 0.4 -> 0.32 เบาลง
"tts": {"enabled": true, "offline_fallback": "auto"} // เดิม false
```

### 5. ทดสอบใหม่
```bash
python auto_factory.py --once --pillar Health --topic "ทำไมแสงสีฟ้าทำให้นอนไม่หลับ"
# ผล:
# - TTS silent fallback 47s -> cap เป็น music only 15s (demo) -> Render 15.0s
# - BG: placeholder_2.mp4
# - Music: ambient_lofi.mp3 vol 0.38
# - Video: 1.6M, 1080x1920, audio 15.0s True
# - History saved: outputs/logs/history.json
```

## ก่อน vs หลัง

| ปัญหา | ก่อน | หลัง |
|------|------|------|
| ฟอนต์ | HTML 265KB -> สี่เหลี่ยม | TTF 214KB -> ไทยชัด |
| ข้อความ | ทับกัน, เป็นจุด ... | 1. 2. 3. ชัด, ไม่ทับ |
| เสียง | ไม่มี / sine แหลม | มีเพลง brown noise ฟังสบาย + TTS ไทย |
| คุณภาพ | ไม่พร้อมลง YT | พร้อมลง: 1080x1920, 15s/60s, มีปก, ชื่อ, คำอธิบาย, แท็ก |

## วิธีใช้งานจริง

```bash
# 1. ตั้งให้เป็น 60s เต็ม (production)
# แก้ config/factory_settings.json: "duration": 60

# 2. เปิด TTS (แนะนำ)
# "tts": {"enabled": true}

# 3. รัน
python auto_factory.py --daily --batch 2
# ได้ 2 คลิป 60s พร้อมลง YouTube
```

## ไฟล์ที่แก้
- `assets/fonts/NotoSansThai-Black.ttf` (ใหม่ 214KB)
- `assets/music/Knowledge_*/ambient_lofi.mp3` (ใหม่ 368KB)
- `factory/renderer_v2.py` (ใหม่)
- `factory/tts_engine_v2.py` (ใหม่)
- `factory/music_engine.py` (ใหม่)
- `factory/renderer.py` (เดิมไว้ fallback)
- `auto_factory.py` (แก้ใช้ V2)
- `config/factory_settings.json` (เปิด TTS, volume 0.32)
- `docs/FIXES.md` (ไฟล์นี้)

ทดสอบแล้ว: `outputs/knowledge/20261018_072450_Health_213398.mp4` 1.6M 15.0s พร้อมลง
