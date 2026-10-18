#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_factory.py - โรงงานผลิตคลิป "รู้หรือไม่ใน 1 นาที" อัตโนมัติ 100%

วิธีใช้:
  python auto_factory.py --once --pillar Psychology        # ทำ 1 คลิปทดสอบ
  python auto_factory.py --once --topic "ทำไมเราถึงฝัน"   # ทำหัวข้อที่กำหนด
  python auto_factory.py --daily --batch 2                 # ทำวันละ 2 คลิป + ตั้งเวลา
  python auto_factory.py --daily --batch 2 --upload        # ทำ + อัพโหลดเลย
  python auto_factory.py --schedule-only                   # สร้างตารางอย่างเดียว
  python auto_factory.py --check-assets                    # เช็คว่ามีวัตถุดิบพอไหม

ระบบจะอ่าน:
  - config/knowledge.json (4 เสาหลัก 40 หัวข้อ)
  - config/factory_settings.json (ตั้งค่าโรงงาน)
  - config/settings.json (API keys เดิม)
"""

import os
import sys
import json
import argparse
import random
import re
from datetime import datetime
from pathlib import Path

# เพิ่ม path
sys.path.insert(0, ".")

from factory.config import get_factory_settings, get_knowledge, get_settings, get_groq_key, get_pexels_key, get_pixabay_key
from factory.knowledge import pick_topic, get_pillar_for_today, load_knowledge, load_history, mark_topic_used, get_pillar_info
from factory.script_engine import write_script, estimate_duration
from factory.tts_engine import generate_tts
from factory.media_engine import ensure_assets_for_pillar, pick_background_video, get_music_for_pillar
from factory.metadata_engine import build_all_metadata
from factory.renderer import KnowledgeRenderer
from factory.scheduler import generate_schedule, load_schedule
from factory.uploader import auto_upload, save_upload_log

# สี log
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log(msg, color=""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")

def ensure_dirs():
    for d in ["outputs/knowledge", "outputs/thumbnails", "outputs/logs", "assets/backgrounds", "assets/music", "outputs"]:
        os.makedirs(d, exist_ok=True)

def check_assets_report():
    """เช็คว่ามีวิดีโอ/เพลงพอไหม"""
    print("\n" + "="*60)
    print("🔍 ตรวจวัตถุดิบโรงงาน")
    print("="*60)
    knowledge = get_knowledge()
    pillars = knowledge.get("pillars", {})
    for pillar_id, info in pillars.items():
        from factory.media_engine import get_local_videos, get_music_for_pillar
        vids = get_local_videos(pillar_id)
        music = get_music_for_pillar(pillar_id)
        status = f"{GREEN}✅ พอ{RESET}" if len(vids) >= 3 else f"{YELLOW}⚠️ น้อย{RESET}" if len(vids) > 0 else f"{RED}❌ ไม่มี{RESET}"
        print(f"  {info.get('emoji','')} {pillar_id} ({info.get('name_th')}) - วิดีโอ: {len(vids)} {status} | เพลง: {'มี' if music else 'ไม่มี'}")
        if len(vids) == 0:
            dir_map = {"Psychology": "Knowledge_Psychology", "Money": "Knowledge_Money", "Health": "Knowledge_Health", "History": "Knowledge_History"}
            print(f"      → วางวิดีโอที่: assets/backgrounds/{dir_map.get(pillar_id, pillar_id)}/")
    print("="*60 + "\n")

def produce_one(topic=None, pillar=None, output_dir="outputs/knowledge", dry_run=False):
    """
    ผลิต 1 คลิปเต็ม
    return: (success, output_path, metadata)
    """
    factory_settings = get_factory_settings()
    knowledge = get_knowledge()
    settings = get_settings()
    
    groq_key = get_groq_key()
    pexels_key = get_pexels_key()
    pixabay_key = get_pixabay_key()
    
    # 1. เลือกหัวข้อ
    if topic and pillar:
        sel_pillar, sel_topic = pillar, topic
        log(f"📌 หัวข้อกำหนด: [{sel_pillar}] {sel_topic}", CYAN)
    elif topic:
        sel_pillar = get_pillar_for_today(knowledge)
        sel_topic = topic
        log(f"📌 หัวข้อกำหนด: {sel_topic} → เดาหมวด: {sel_pillar}", CYAN)
    else:
        if pillar:
            # เลือกหัวข้อใน pillar ที่กำหนด
            sel_pillar, sel_topic = pick_topic(pillar=pillar, knowledge=knowledge)
        else:
            # เลือกตามวัน
            sel_pillar, sel_topic = pick_topic(knowledge=knowledge)
        log(f"📌 เลือกหัวข้อ: [{sel_pillar}] {sel_topic}", CYAN)
    
    pillar_info = get_pillar_info(sel_pillar, knowledge)
    
    # 2. เขียนบท
    log(f"✍️  เขียนบท 60วิ...", YELLOW)
    script = write_script(sel_topic, sel_pillar, groq_key)
    log(f"   Hook: {script['hook']}", "")
    log(f"   Title: {script['title']}", "")
    est = estimate_duration(script["full_script"])
    log(f"   ประมาณ {est:.0f}วิ ({len(script['full_script'])} ตัวอักษร)", "")
    
    # 3. ทำ Metadata
    metadata = build_all_metadata(script, sel_pillar)
    log(f"📝 Title: {metadata['title']}", GREEN)
    
    # ตั้งชื่อไฟล์ (ใช้เวลากับ pillar เป็นหลัก กันชื่อไทยพัง)
    safe_topic = re_safe_filename(sel_topic)[:18]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # ใช้ชื่อไฟล์ปลอดภัย: timestamp + pillar + hash กันซ้ำ
    import hashlib
    topic_hash = hashlib.md5(sel_topic.encode('utf-8')).hexdigest()[:6]
    filename = f"{timestamp}_{sel_pillar}_{topic_hash}.mp4"
    # เก็บชื่อไทยไว้ใน metadata แทน
    output_path = os.path.join(output_dir, filename)
    
    if dry_run:
        log(f"[DRY RUN] จะบันทึกที่: {output_path}", YELLOW)
        log(f"[DRY RUN] Script: {script['full_script'][:150]}...", "")
        return True, output_path, metadata
    
    # 4. TTS
    tts_enabled = factory_settings.get("tts", {}).get("enabled", True)
    tts_voice = factory_settings.get("tts", {}).get("voice", "th-TH-NiwatNeural")
    audio_path = None
    audio_duration = None
    
    if tts_enabled:
        log(f"🔊 พากย์เสียง {tts_voice}...", YELLOW)
        audio_path = os.path.join(output_dir, f"tts_{timestamp}.mp3")
        ok, dur = generate_tts(script["full_script"], audio_path, voice=tts_voice)
        if ok:
            audio_duration = dur
            log(f"   ✅ เสียง {dur:.1f}วิ" if dur else "   ✅ เสียงเสร็จ", GREEN)
            # ตรวจความยาวแล้วปรับ duration
            if dur:
                factory_settings["video"]["duration"] = int(min(62, max(45, dur + 2)))
        else:
            log(f"   ⚠️ TTS ล้มเหลว จะใช้แค่เพลงพื้นหลัง", YELLOW)
            audio_path = None
    else:
        log(f"🔇 TTS ปิด จะใช้แค่เพลง", YELLOW)
    
    # 5. หาวิดีโอพื้นหลัง
    log(f"🎞️  หาวิดีโอพื้นหลัง {pillar_info.get('name_th', sel_pillar)}...", YELLOW)
    auto_dl = factory_settings.get("generation", {}).get("auto_download_assets", True)
    bg_path = pick_background_video(sel_pillar, pexels_key, pixabay_key, auto_download=auto_dl)
    if not bg_path:
        log(f"❌ ไม่มีวิดีโอพื้นหลังสำหรับ {sel_pillar}", RED)
        # ลองหา fallback
        from factory.media_engine import get_local_videos
        fallback = get_local_videos(sel_pillar)
        if fallback:
            bg_path = random.choice(fallback)
        else:
            # หาจากทุกหมวด
            all_vids = []
            for p in ["Psychology", "Money", "Health", "History"]:
                all_vids.extend(get_local_videos(p))
            if all_vids:
                bg_path = random.choice(all_vids)
                log(f"   → ใช้วิดีโอสำรอง: {os.path.basename(bg_path)}", YELLOW)
            else:
                log(f"❌ ไม่มีวิดีโอเลยสักหมวด! ใส่ไฟล์ .mp4 ลง assets/backgrounds/ ก่อน", RED)
                return False, None, None
    log(f"   ✅ BG: {os.path.basename(bg_path)}", GREEN)
    
    # เพลง
    music_path = get_music_for_pillar(sel_pillar)
    if music_path:
        log(f"   🎵 Music: {os.path.basename(music_path)}", "")
    else:
        log(f"   🎵 ไม่มีเพลง จะใช้เสียงพากย์อย่างเดียว", YELLOW)
    
    # 6. เรนเดอร์
    log(f"🎬 เรนเดอร์วิดีโอ 1080x1920...", CYAN)
    renderer = KnowledgeRenderer(factory_settings)
    # ปรับ duration ตามเสียงจริงถ้ามี
    if audio_duration:
        renderer.duration = int(min(62, max(50, audio_duration + 3)))
    
    ok = renderer.render(bg_path, audio_path, script, metadata, output_path, music_path)
    
    if ok and os.path.exists(output_path):
        log(f"✅ เสร็จ! {output_path} ({os.path.getsize(output_path)//1024} KB)", GREEN)
        
        # ลบไฟล์ tts ชั่วคราว
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        
        # บันทึก history
        try:
            history = load_history()
            if sel_topic not in history.get("used_topics", []):
                if "used_topics" not in history:
                    history["used_topics"] = []
                history["used_topics"].append(sel_topic)
                # เซฟ used_topics ทันที
                from factory.config import save_json as _save_json
                _save_json("outputs/logs/history.json", history)
                log(f"   📝 บันทึก used_topics: {sel_topic[:30]}", "")
            # โหลดใหม่เพื่อกันทับ
            history = load_history()
            history_path = "outputs/logs/history.json"
            entry = {
                "file": os.path.basename(output_path),
                "full_path": output_path,
                "theme": sel_pillar,
                "pillar_th": pillar_info.get("name_th", sel_pillar),
                "topic": sel_topic,
                "hook": script["hook"],
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "script": script["full_script"],
                "duration": renderer.duration,
                "created_at": datetime.now().isoformat(),
                "bg_file": os.path.basename(bg_path),
                "music_file": os.path.basename(music_path) if music_path else None
            }
            if "generated" not in history:
                history["generated"] = []
            history["generated"].append(entry)
            if len(history["generated"]) > 1000:
                history["generated"] = history["generated"][-500:]
            _save_json(history_path, history)
            log(f"   📝 บันทึก log สำเร็จ ({len(history['generated'])} รายการ)", GREEN)
            
            # บันทึกไฟล์ .json คู่กับวิดีโอ
            meta_path = output_path.replace(".mp4", ".json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            log(f"   📝 Metadata: {os.path.basename(meta_path)}", "")
        except Exception as e:
            log(f"   ⚠️ บันทึก log ล้มเหลว: {e}", YELLOW)
            import traceback; traceback.print_exc()
        
        return True, output_path, metadata
    else:
        log(f"❌ เรนเดอร์ล้มเหลว", RED)
        return False, None, None

def re_safe_filename(s):
    """ทำชื่อไฟล์ให้ปลอดภัย"""
    import re
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', s)
    s = s.replace(" ", "_").replace("/", "_")
    # ลบอีโมจิออก
    s = "".join(c for c in s if ord(c) < 0x1F600 or ord(c) > 0x1F64F)
    # ตัดให้สั้น
    return s.strip("_")[:30]

def run_daily_batch(batch_size=2, upload=False, dry_run=False):
    """รันผลิต batch ตามจำนวนที่กำหนด + ตั้งเวลา"""
    log(f"🏭 เริ่มโรงงาน Batch {batch_size} คลิป | Upload={upload} | DryRun={dry_run}", CYAN)
    print("="*60)
    check_assets_report()
    
    factory_settings = get_factory_settings()
    output_dir = factory_settings.get("paths", {}).get("outputs", "outputs/knowledge")
    
    success_files = []
    for i in range(batch_size):
        log(f"—— คลิป {i+1}/{batch_size} ——", CYAN)
        ok, path, meta = produce_one(output_dir=output_dir, dry_run=dry_run)
        if ok:
            success_files.append(os.path.basename(path))
            log(f"✅ คลิป {i+1} เสร็จ: {os.path.basename(path)}", GREEN)
        else:
            log(f"❌ คลิป {i+1} ล้มเหลว", RED)
        print()
    
    log(f"🏁 สรุป: สำเร็จ {len(success_files)}/{batch_size}", GREEN if len(success_files)==batch_size else YELLOW)
    
    # ตั้งเวลาลง
    if success_files and not dry_run:
        auto_schedule = factory_settings.get("generation", {}).get("auto_schedule", True)
        if auto_schedule:
            from factory.scheduler import generate_schedule
            times = factory_settings.get("generation", {}).get("schedule_times", ["07:30", "19:30"])
            log(f"📅 ตั้งเวลาลง: {times}", CYAN)
            generate_schedule(success_files, times_per_day=times)
        
        # อัพโหลด
        if upload:
            log(f"📤 เริ่มอัพโหลด {len(success_files)} คลิป...", CYAN)
            for fname in success_files:
                fpath = os.path.join(output_dir, fname)
                # โหลด metadata
                meta_path = fpath.replace(".mp4", ".json")
                meta = {}
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta = {"title": meta.get("title",""), "description": meta.get("description",""), "tags": meta.get("tags",[])}
                ok, link = auto_upload(fpath, meta)
                save_upload_log("YouTube", fname, "Success" if ok else "Failed", link)
                log(f"   {'✅' if ok else '❌'} {fname} → {link}", GREEN if ok else RED)
    
    return success_files

def main():
    parser = argparse.ArgumentParser(description="Auto Knowledge Factory - โรงงานรู้หรือไม่ 1 นาที")
    parser.add_argument("--once", action="store_true", help="ทำ 1 คลิป")
    parser.add_argument("--pillar", type=str, help="เลือกหมวด: Psychology/Money/Health/History")
    parser.add_argument("--topic", type=str, help="กำหนดหัวข้อเอง")
    parser.add_argument("--daily", action="store_true", help="รันโหมดรายวัน (batch)")
    parser.add_argument("--batch", type=int, default=2, help="จำนวนคลิปต่อวัน (default 2)")
    parser.add_argument("--upload", action="store_true", help="อัพโหลดหลังทำเสร็จ")
    parser.add_argument("--dry-run", action="store_true", help="ทดสอบไม่เรนเดอร์จริง")
    parser.add_argument("--schedule-only", action="store_true", help="สร้างตารางจากไฟล์ที่มีอยู่")
    parser.add_argument("--check-assets", action="store_true", help="ตรวจวัตถุดิบ")
    parser.add_argument("--list-topics", action="store_true", help="ดูหัวข้อทั้งหมด")
    parser.add_argument("--output", type=str, default=None, help="โฟลเดอร์ output")
    
    args = parser.parse_args()
    
    ensure_dirs()
    
    if args.check_assets:
        check_assets_report()
        return
    
    if args.list_topics:
        k = get_knowledge()
        for pillar, topics in k.get("topics", {}).items():
            info = k.get("pillars", {}).get(pillar, {})
            print(f"\n{info.get('emoji','')} {pillar} ({info.get('name_th')}):")
            for t in topics:
                print(f"  - {t}")
        return
    
    if args.schedule_only:
        # สร้างตารางจากไฟล์ที่มีอยู่แล้ว
        output_dir = args.output or get_factory_settings().get("paths", {}).get("outputs", "outputs/knowledge")
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith(".mp4")]
            if files:
                generate_schedule(files)
            else:
                print(f"ไม่มีไฟล์ใน {output_dir}")
        return
    
    if args.once:
        pillar = args.pillar
        # validate pillar
        if pillar and pillar not in ["Psychology", "Money", "Health", "History"]:
            # ลองแปลงไทย
            thai_map = {"จิตวิทยา": "Psychology", "เงิน": "Money", "สุขภาพ": "Health", "ประวัติศาสตร์": "History"}
            pillar = thai_map.get(pillar, pillar)
        
        output_dir = args.output or get_factory_settings().get("paths", {}).get("outputs", "outputs/knowledge")
        ok, path, meta = produce_one(topic=args.topic, pillar=pillar, output_dir=output_dir, dry_run=args.dry_run)
        if ok:
            print("\n" + "="*60)
            print(f"{GREEN}✅ เสร็จ! ไฟล์: {path}{RESET}")
            print(f"   Title: {meta['title']}")
            print(f"   Tags: {', '.join(meta['tags'][:5])}")
            print("="*60)
        return
    
    if args.daily:
        run_daily_batch(batch_size=args.batch, upload=args.upload, dry_run=args.dry_run)
        return
    
    # ถ้าไม่ใส่อะไรเลย ให้ทำ 1 คลิป
    print(f"{YELLOW}ไม่ได้ระบุโหมด → รัน --once 1 คลิปให้ดู{YELLOW}")
    ok, path, meta = produce_one(dry_run=args.dry_run)
    if ok:
        print(f"{GREEN}✅ {path}{RESET}")

if __name__ == "__main__":
    main()
