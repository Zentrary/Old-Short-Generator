"""
uploader.py - อัพโหลดอัตโนมัติ
รองรับ YouTube API (ถ้ามี credentials) + Selenium fallback
Reuse SocialMediaAutomator จาก main.py
"""
import os
import json

# พยายาม import Selenium ถ้ามี
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    SELENIUM_AVAILABLE = True
except:
    SELENIUM_AVAILABLE = False

def upload_via_api(video_path, metadata, credentials_path="config/youtube_credentials.json"):
    """
    อัพโหลดผ่าน YouTube Data API v3
    ต้องมี credentials.json จาก Google Cloud Console
    """
    # ถ้ายังไม่มี credentials ให้ข้าม
    if not os.path.exists(credentials_path):
        print(f"[Uploader] YouTube API credentials not found: {credentials_path}")
        print("         → ไปสร้างที่ https://console.cloud.google.com/apis/credentials")
        return False, "No credentials"
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        
        # โหลด token
        with open(credentials_path, "r") as f:
            creds_data = json.load(f)
        
        creds = Credentials.from_authorized_user_file(credentials_path, ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)
        
        title = metadata.get("title", "รู้หรือไม่?")
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])
        # ล้าง # ออกจาก tags สำหรับ API
        tags = [t.replace("#", "") for t in tags if t]
        
        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags[:15],
                "categoryId": "27"  # Education
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        
        video_id = response.get("id", "")
        print(f"[Uploader] ✅ YouTube API uploaded: https://youtu.be/{video_id}")
        return True, f"https://youtu.be/{video_id}"
        
    except Exception as e:
        print(f"[Uploader] YouTube API error: {e}")
        return False, str(e)

def upload_via_selenium(video_path, metadata, platform="Shorts", headless=False):
    """
    อัพโหลดผ่าน Selenium (reuse main.py logic)
    """
    if not SELENIUM_AVAILABLE:
        print("[Uploader] Selenium not available")
        return False, "Selenium not installed"
    
    # Import แบบ lazy เพื่อไม่ให้ main.py ต้องรัน
    import sys
    sys.path.insert(0, ".")
    try:
        from main import SocialMediaAutomator
        
        def log(msg):
            print(f"[Uploader][Selenium] {msg}")
        
        bot = SocialMediaAutomator(log_callback=log, headless=headless)
        if not bot.start_browser():
            return False, "Browser launch failed"
        
        # เตรียม caption
        caption = f"{metadata.get('title','')}\n\n{metadata.get('description','')[:200]}"
        
        # เลือก platform
        platform_map = {
            "Shorts": "Shorts",
            "YouTube": "Shorts",
            "TikTok": "TikTok",
            "Instagram": "Instagram"
        }
        target = platform_map.get(platform, "Shorts")
        
        # ต้องมีไฟล์จริง
        abs_path = os.path.abspath(video_path)
        if not os.path.exists(abs_path):
            return False, f"File not found: {abs_path}"
        
        # เรียก upload
        if target == "TikTok":
            ok = bot.upload_tiktok(abs_path, caption)
        elif target == "Instagram":
            ok = bot.upload_instagram(abs_path, caption)
        elif target == "Shorts":
            ok = bot.upload_shorts(abs_path, caption)
        else:
            ok = False
        
        bot.close()
        return ok, "Selenium done" if ok else "Selenium failed"
        
    except Exception as e:
        print(f"[Uploader] Selenium error: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def auto_upload(video_path, metadata, prefer_api=True):
    """
    ลอง API ก่อน ถ้าไม่ได้ให้ใช้ Selenium
    """
    if prefer_api:
        ok, msg = upload_via_api(video_path, metadata)
        if ok:
            return True, msg
        print(f"[Uploader] API failed ({msg}), falling back to Selenium...")
    
    return upload_via_selenium(video_path, metadata)

def save_upload_log(platform, filename, status, link=""):
    log_path = "config/social_history.json"
    entry = {
        "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform,
        "filename": filename,
        "status": status,
        "link": link
    }
    try:
        data = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        data.append(entry)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Uploader] Log save error: {e}")
