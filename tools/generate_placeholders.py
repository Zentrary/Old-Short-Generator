"""
generate_placeholders.py - สร้างวิดีโอ/เพลง placeholder สำหรับทดสอบโรงงาน
รัน: python tools/generate_placeholders.py
"""
import os
import numpy as np

try:
    from moviepy.editor import ColorClip, AudioClip
    MOVIEPY = True
except:
    try:
        from moviepy import ColorClip, AudioClip
        MOVIEPY = True
    except:
        MOVIEPY = False

# สีตามหมวด
COLORS = {
    "Knowledge_Psychology": (124, 77, 255),   # ม่วง
    "Knowledge_Money": (0, 200, 83),          # เขียว
    "Knowledge_Health": (255, 61, 0),         # แดง
    "Knowledge_History": (255, 160, 0),      # ส้ม
}

def ensure_dirs():
    for pillar in COLORS:
        os.makedirs(f"assets/backgrounds/{pillar}", exist_ok=True)
        os.makedirs(f"assets/music/{pillar}", exist_ok=True)
    os.makedirs("outputs/knowledge", exist_ok=True)

def create_bg_video(path, color, duration=10):
    """สร้างวิดีโอสีพื้น 9:16"""
    if not MOVIEPY:
        print("MoviePy not installed, skip video")
        return False
    try:
        clip = ColorClip(size=(1080, 1920), color=color, duration=duration)
        # เพิ่ม gradient ง่ายๆ ด้วยการทำให้สีค่อยๆ เข้ม
        clip.write_videofile(path, fps=24, codec='libx264', audio=False, logger=None)
        clip.close()
        print(f"✅ BG: {path}")
        return True
    except Exception as e:
        print(f"❌ BG error {path}: {e}")
        return False

def create_music(path, freq=440, duration=60):
    """สร้างเพลง Lo-fi ง่ายๆ (sine wave)"""
    if not MOVIEPY:
        return False
    try:
        def make_frame(t):
            # สร้างเสียงหลายความถี่ผสมกัน
            return np.array([0.1 * np.sin(2 * np.pi * 220 * t) + 0.05 * np.sin(2 * np.pi * 440 * t)])
        
        audio = AudioClip(make_frame, duration=duration)
        audio.write_audiofile(path, fps=44100, logger=None)
        audio.close()
        print(f"✅ Music: {path}")
        return True
    except Exception as e:
        print(f"❌ Music error {path}: {e}")
        return False

def main():
    ensure_dirs()
    print("🎨 สร้าง placeholder assets...")
    
    # สร้างวิดีโอ 2 ตัว/หมวด
    for pillar, color in COLORS.items():
        for i in range(2):
            bg_path = f"assets/backgrounds/{pillar}/placeholder_{i+1}.mp4"
            if not os.path.exists(bg_path):
                create_bg_video(bg_path, color)
            else:
                print(f"⏭️  Skip exists: {bg_path}")
    
    # สร้างเพลง 1 ตัว/หมวด
    for pillar in COLORS:
        music_path = f"assets/music/{pillar}/placeholder_lofi.mp3"
        if not os.path.exists(music_path):
            create_music(music_path)
        else:
            print(f"⏭️  Skip exists: {music_path}")
    
    print("\n✅ เสร็จ! โรงงานพร้อมรัน: python auto_factory.py --once --dry-run")

if __name__ == "__main__":
    main()
