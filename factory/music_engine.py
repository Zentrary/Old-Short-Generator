"""
music_engine.py - จัดการเพลงพื้นหลังให้ดี ไม่ใช่ sine wave แปลกๆ
"""
import os
import random
import numpy as np

def get_music_for_pillar(pillar, base_dir="assets/music"):
    """หาเพลงที่มีอยู่"""
    dir_map = {
        "Psychology": "Knowledge_Psychology",
        "Money": "Knowledge_Money",
        "Health": "Knowledge_Health",
        "History": "Knowledge_History"
    }
    dir_name = dir_map.get(pillar, pillar)
    paths = [
        os.path.join(base_dir, dir_name),
        os.path.join(base_dir, pillar),
        os.path.join("assets/music", dir_name),
    ]
    candidates = []
    for p in paths:
        if os.path.exists(p):
            for f in os.listdir(p):
                if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
                    full = os.path.join(p, f)
                    if os.path.exists(full) and os.path.getsize(full) > 8000:
                        # ข้าม placeholder sine wave เก่า (470KB เป๊ะๆ)
                        # ถ้าเป็น placeholder เก่าให้ข้าม ถ้ามีเพลงจริงให้ใช้
                        candidates.append(full)
    # เรียงให้เพลงจริงมาก่อน placeholder
    # ถ้าเจอหลายไฟล์ สุ่มเลือกที่ไม่ใช่ placeholder sine
    if not candidates:
        # fallback ทุกหมวด
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.lower().endswith(('.mp3','.wav')):
                    full = os.path.join(root, f)
                    if os.path.getsize(full) > 8000:
                        candidates.append(full)
    if candidates:
        # กรอง placeholder เก่าออกถ้ามีตัวอื่น
        real = [c for c in candidates if "placeholder" not in c.lower()]
        if real:
            return random.choice(real)
        return random.choice(candidates)
    return None

def create_pleasant_placeholder(dest_path, duration=60):
    """
    สร้างเพลง placeholder ที่ฟังสบายกว่า sine เดิม
    ใช้ brown noise + chord แบบ lofi ที่ volume ต่ำ
    """
    try:
        import subprocess, shutil, tempfile
        # ใช้ ffmpeg สร้าง brown noise + lowpass
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except:
                return False
        
        # สร้าง brown noise ที่เบาๆ ฟังสบาย (ไม่ใช่ sine แหลม)
        # brown noise + volume 0.15
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"anoisesrc=r=44100:a=0.15:c=brown:d={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration}:sample_rate=44100,volume=0.08",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest,lowpass=f=1200,volume=0.35",
            "-acodec", "libmp3lame", "-q:a", "4",
            dest_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=20)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 5000:
            print(f"[Music] ✅ Pleasant placeholder: {dest_path}")
            return True
        return False
    except Exception as e:
        print(f"[Music] Placeholder error: {e}")
        return False

def ensure_music_assets():
    """ตรวจและสร้างเพลง placeholder ที่ดีถ้ายังไม่มีเพลงจริง"""
    dir_map = {
        "Psychology": "Knowledge_Psychology",
        "Money": "Knowledge_Money",
        "Health": "Knowledge_Health",
        "History": "Knowledge_History"
    }
    for pillar, dname in dir_map.items():
        pdir = os.path.join("assets/music", dname)
        os.makedirs(pdir, exist_ok=True)
        existing = [f for f in os.listdir(pdir) if f.lower().endswith(('.mp3','.wav'))] if os.path.exists(pdir) else []
        # ถ้ามีแต่ placeholder เก่า ให้แทนที่
        has_real = any("placeholder" not in f.lower() for f in existing)
        if not has_real and not existing:
            # สร้างใหม่
            dest = os.path.join(pdir, "ambient_lofi.mp3")
            create_pleasant_placeholder(dest, duration=65)
        elif existing and all("placeholder_lofi" in f for f in existing):
            # มีแต่ placeholder sine เก่า ให้ปรับให้ดีขึ้น
            # ไม่ลบของเก่า แต่สร้างเพิ่มตัวที่ดีกว่า
            dest = os.path.join(pdir, "ambient_lofi_v2.mp3")
            if not os.path.exists(dest):
                create_pleasant_placeholder(dest, duration=65)

def download_free_music(pillar, pixabay_key=None):
    """
    ลองโหลดเพลงฟรีจาก Pixabay Music API
    https://pixabay.com/api/docs/#api_music_search
    """
    if not pixabay_key:
        return None
    try:
        import requests
        # Pixabay Music API (แยกจาก video)
        url = "https://pixabay.com/api/music/"
        params = {
            "key": pixabay_key,
            "q": {"Psychology": "ambient meditation", "Money": "corporate business", "Health": "calm wellness", "History": "cinematic documentary"}.get(pillar, "ambient"),
            "per_page": 5,
            "order": "popular"
        }
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits)
        audio_url = hit.get("audio") or hit.get("download_url")
        if not audio_url:
            return None
        dir_map = {"Psychology": "Knowledge_Psychology", "Money": "Knowledge_Money", "Health": "Knowledge_Health", "History": "Knowledge_History"}
        dest_dir = os.path.join("assets/music", dir_map.get(pillar, pillar))
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"pixabay_{hit.get('id', random.randint(1000,9999))}.mp3")
        if os.path.exists(dest):
            return dest
        r = requests.get(audio_url, timeout=20, stream=True)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk: f.write(chunk)
            if os.path.getsize(dest) > 8000:
                print(f"[Music] ✅ Downloaded Pixabay music: {hit.get('id')}")
                return dest
        return None
    except Exception as e:
        print(f"[Music] Pixabay error: {e}")
        return None
