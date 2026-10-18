"""
media_engine.py - หา/ดาวน์โหลดวิดีโอพื้นหลังอัตโนมัติ
Reuse logic จาก main.py AssetDownloader แต่ทำแบบ headless
"""
import os
import random
import requests
import json

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except:
    CLOUDSCRAPER_AVAILABLE = False

PEXELS_API = "https://api.pexels.com/videos/search"
PIXABAY_API = "https://pixabay.com/api/videos/"

# แมป pillar -> คำค้น + โฟลเดอร์
PILLAR_SEARCH = {
    "Psychology": ["psychology brain", "mind thinking", "people talking", "human emotion"],
    "Money": ["money finance", "business success", "investment chart", "wealth"],
    "Health": ["healthy lifestyle", "medical health", "fitness gym", "sleep wellness"],
    "History": ["history ancient", "science space", "nature document", "discovery"]
}

PILLAR_DIR_MAP = {
    "Psychology": "Knowledge_Psychology",
    "Money": "Knowledge_Money",
    "Health": "Knowledge_Health",
    "History": "Knowledge_History"
}

def get_local_videos(pillar, base_dir="assets/backgrounds"):
    """หาวิดีโอที่มีในเครื่อง"""
    dir_name = PILLAR_DIR_MAP.get(pillar, pillar)
    pillar_path = os.path.join(base_dir, dir_name)
    
    # fallback ถ้าไม่มีโฟลเดอร์ Knowledge_* ให้ไปหาใน Nature/Life
    if not os.path.exists(pillar_path):
        # ลองหาในโฟลเดอร์เดิม
        fallback_dirs = ["Nature", "Life", "Motivation", "Business"]
        videos = []
        for fd in fallback_dirs:
            p = os.path.join(base_dir, fd)
            if os.path.exists(p):
                for f in os.listdir(p):
                    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        videos.append(os.path.join(p, f))
        return videos
    
    videos = []
    if os.path.exists(pillar_path):
        for f in os.listdir(pillar_path):
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                full = os.path.join(pillar_path, f)
                # ข้ามไฟล์ Nig.txt
                if os.path.getsize(full) > 10000:
                    videos.append(full)
    return videos

def fetch_pexels_videos(query, api_key, per_page=5):
    """ดึงวิดีโอจาก Pexels"""
    if not api_key:
        return []
    
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "portrait",
        "size": "medium"
    }
    
    try:
        resp = requests.get(PEXELS_API, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[Media] Pexels {resp.status_code}: {resp.text[:200]}")
            return []
        
        data = resp.json()
        videos = data.get("videos", [])
        results = []
        for v in videos:
            # เลือกไฟล์ portrait ที่เล็กสุดที่ชัด
            files = v.get("video_files", [])
            # หาไฟล์ vertical
            best = None
            for f in files:
                w, h = f.get("width", 0), f.get("height", 0)
                if h > w and w >= 720:  # vertical
                    if best is None or f["width"] < best["width"]:
                        best = f
            if best:
                results.append({
                    "url": best["link"],
                    "width": best["width"],
                    "height": best["height"],
                    "duration": v.get("duration", 0),
                    "source": "pexels",
                    "id": v.get("id")
                })
        print(f"[Media] Pexels '{query}' → {len(results)} videos")
        return results
    except Exception as e:
        print(f"[Media] Pexels error: {e}")
        return []

def fetch_pixabay_videos(query, api_key, per_page=5):
    """ดึงวิดีโอจาก Pixabay"""
    if not api_key:
        return []
    
    params = {
        "key": api_key,
        "q": query,
        "video_type": "all",
        "per_page": per_page,
        "orientation": "vertical"
    }
    
    try:
        resp = requests.get(PIXABAY_API, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[Media] Pixabay {resp.status_code}")
            return []
        
        data = resp.json()
        hits = data.get("hits", [])
        results = []
        for h in hits:
            videos = h.get("videos", {})
            # เลือก medium หรือ large ที่เป็น vertical
            for k in ["medium", "large", "small"]:
                v = videos.get(k, {})
                url = v.get("url", "")
                w, h_ = v.get("width", 0), v.get("height", 0)
                if url and h_ > w:
                    results.append({
                        "url": url,
                        "width": w,
                        "height": h_,
                        "duration": h.get("duration", 0),
                        "source": "pixabay",
                        "id": h.get("id")
                    })
                    break
        print(f"[Media] Pixabay '{query}' → {len(results)} videos")
        return results
    except Exception as e:
        print(f"[Media] Pixabay error: {e}")
        return []

def download_video(url, dest_path, timeout=30):
    """ดาวน์โหลดวิดีโอ 1 ไฟล์"""
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # ลอง cloudscraper ก่อน ถ้ามี
        if CLOUDSCRAPER_AVAILABLE and "pixabay" in url:
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, headers=headers, timeout=timeout, stream=True)
        else:
            resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if resp.status_code != 200:
            print(f"[Media] Download {resp.status_code}: {url[:60]}")
            return False
        
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            print(f"[Media] ✅ Downloaded: {os.path.basename(dest_path)}")
            return True
        else:
            print(f"[Media] ❌ File too small: {dest_path}")
            return False
    except Exception as e:
        print(f"[Media] Download error: {e}")
        return False

def ensure_assets_for_pillar(pillar, pexels_key=None, pixabay_key=None, min_count=5, auto_download=True):
    """
    ตรวจว่ามีวิดีโอพอไหม ถ้าไม่พอให้โหลดเพิ่ม
    return: list of local video paths
    """
    videos = get_local_videos(pillar)
    print(f"[Media] Local videos for {pillar}: {len(videos)}")
    
    if len(videos) >= min_count or not auto_download:
        return videos
    
    # ต้องโหลดเพิ่ม
    needed = min_count - len(videos)
    queries = PILLAR_SEARCH.get(pillar, ["nature"])
    query = random.choice(queries)
    
    dir_name = PILLAR_DIR_MAP.get(pillar, pillar)
    dest_dir = os.path.join("assets/backgrounds", dir_name)
    os.makedirs(dest_dir, exist_ok=True)
    
    # ลอง Pexels ก่อน
    candidates = []
    if pexels_key:
        candidates = fetch_pexels_videos(query, pexels_key, per_page=needed*2)
    
    # ถ้าไม่ได้ ลอง Pixabay
    if not candidates and pixabay_key:
        candidates = fetch_pixabay_videos(query, pixabay_key, per_page=needed*2)
    
    downloaded = 0
    for item in candidates[:needed]:
        ext = ".mp4"
        filename = f"{item['source']}_{item['id']}_{random.randint(1000,9999)}{ext}"
        dest = os.path.join(dest_dir, filename)
        if download_video(item["url"], dest):
            videos.append(dest)
            downloaded += 1
            if downloaded >= needed:
                break
    
    print(f"[Media] Total after download: {len(videos)}")
    return videos

def pick_background_video(pillar, pexels_key=None, pixabay_key=None, auto_download=True):
    """สุ่มเลือกวิดีโอ 1 ตัวสำหรับ 1 คลิป"""
    videos = ensure_assets_for_pillar(pillar, pexels_key, pixabay_key, auto_download=auto_download)
    if not videos:
        print(f"[Media] ❌ No videos for {pillar}")
        return None
    return random.choice(videos)

def get_music_for_pillar(pillar, base_dir="assets/music"):
    """หาวิดีโอเพลงประกอบ (Lo-fi เบาๆ)"""
    dir_name = PILLAR_DIR_MAP.get(pillar, pillar)
    pillar_path = os.path.join(base_dir, dir_name)
    
    # ถ้าไม่มีโฟลเดอร์ Knowledge ให้ fallback
    candidates = []
    if os.path.exists(pillar_path):
        for f in os.listdir(pillar_path):
            if f.lower().endswith(('.mp3', '.wav', '.ogg')):
                full = os.path.join(pillar_path, f)
                if os.path.getsize(full) > 5000:
                    candidates.append(full)
    
    if not candidates:
        # หาเพลงทั่วไป
        fallback_dirs = ["Nature", "Life", "Motivation", "Business"]
        for fd in fallback_dirs:
            p = os.path.join(base_dir, fd)
            if os.path.exists(p):
                for f in os.listdir(p):
                    if f.lower().endswith(('.mp3', '.wav')):
                        full = os.path.join(p, f)
                        if os.path.getsize(full) > 5000:
                            candidates.append(full)
    
    if candidates:
        return random.choice(candidates)
    return None
