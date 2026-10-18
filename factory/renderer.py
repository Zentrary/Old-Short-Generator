"""
renderer.py - เรนเดอร์วิดีโอแนวตั้ง 9:16 สำหรับความรู้ 1 นาที
Reuse โค้ด Thai rendering จาก main.py ทั้งหมด
"""
import os
import random
import re
import math
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageStat
from datetime import datetime

# พยายาม import moviepy ทั้ง 2 แบบ
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        ImageClip, ColorClip, CompositeAudioClip, vfx
    )
    MOVIEPY_AVAILABLE = True
    afx = None
except ImportError:
    try:
        from moviepy import (
            VideoFileClip, AudioFileClip, CompositeVideoClip,
            ImageClip, ColorClip, CompositeAudioClip, vfx, afx
        )
        MOVIEPY_AVAILABLE = True
    except:
        MOVIEPY_AVAILABLE = False
        afx = None
        vfx = None

# === Helper functions จาก main.py (copy มาเพื่อไม่ต้องแก้ main.py) ===

def _mp_apply_effects(clip, effects):
    if hasattr(clip, "with_effects"):
        return clip.with_effects(effects)
    return clip

def _mp_resize(clip, *args, **kwargs):
    if hasattr(clip, "resize"):
        return clip.resize(*args, **kwargs)
    if hasattr(clip, "resized"):
        return clip.resized(*args, **kwargs)
    raise AttributeError("MoviePy resize API not available")

def _mp_subclip(clip, start_time, end_time):
    if hasattr(clip, "subclip"):
        return clip.subclip(start_time, end_time)
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start_time, end_time)
    raise AttributeError("MoviePy subclip API not available")

def _mp_crop(clip, **kwargs):
    if hasattr(clip, "crop"):
        return clip.crop(**kwargs)
    return _mp_apply_effects(clip, [vfx.Crop(**kwargs)])

def _mp_loop_clip(clip, n=None, duration=None):
    if hasattr(clip, "loop"):
        kwargs = {}
        if n is not None: kwargs["n"] = n
        if duration is not None: kwargs["duration"] = duration
        return clip.loop(**kwargs)
    effect_kwargs = {}
    if n is not None: effect_kwargs["n"] = n
    if duration is not None: effect_kwargs["duration"] = duration
    return _mp_apply_effects(clip, [vfx.Loop(**effect_kwargs)])

def _mp_set_position(clip, position):
    if hasattr(clip, "set_position"):
        return clip.set_position(position)
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    raise AttributeError("MoviePy position API not available")

def _mp_set_duration(clip, duration):
    if hasattr(clip, "set_duration"):
        return clip.set_duration(duration)
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    raise AttributeError("MoviePy duration API not available")

def _mp_set_audio(clip, audio):
    if hasattr(clip, "set_audio"):
        return clip.set_audio(audio)
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    raise AttributeError("MoviePy audio API not available")

def _mp_set_start(clip, start_time):
    if hasattr(clip, "set_start"):
        return clip.set_start(start_time)
    if hasattr(clip, "with_start"):
        return clip.with_start(start_time)
    raise AttributeError("MoviePy start API not available")

def _mp_fade_in(clip, duration):
    if hasattr(clip, "fadein"):
        return clip.fadein(duration)
    return _mp_apply_effects(clip, [vfx.FadeIn(duration)])

def _mp_fade_out(clip, duration):
    if hasattr(clip, "fadeout"):
        return clip.fadeout(duration)
    return _mp_apply_effects(clip, [vfx.FadeOut(duration)])

def _mp_speedx(clip, factor):
    if hasattr(clip, "fx"):
        return clip.fx(vfx.speedx, factor)
    return _mp_apply_effects(clip, [vfx.MultiplySpeed(factor=factor)])

def _mp_blackwhite(clip):
    if hasattr(clip, "fx"):
        return clip.fx(vfx.blackwhite)
    return _mp_apply_effects(clip, [vfx.BlackAndWhite()])

def _mp_transform_frames(clip, func):
    if hasattr(clip, "fl_image"):
        return clip.fl_image(func)
    if hasattr(clip, "image_transform"):
        return clip.image_transform(func)
    raise AttributeError("MoviePy frame transform API not available")

def _mp_volumex(audio_clip, factor):
    if hasattr(audio_clip, "volumex"):
        return audio_clip.volumex(factor)
    if afx is not None:
        return _mp_apply_effects(audio_clip, [afx.MultiplyVolume(factor)])
    raise AttributeError("MoviePy volume API not available")

def _mp_audio_fade_in(audio_clip, duration):
    if hasattr(audio_clip, "audio_fadein"):
        return audio_clip.audio_fadein(duration)
    if afx is not None:
        return _mp_apply_effects(audio_clip, [afx.AudioFadeIn(duration)])
    raise AttributeError("MoviePy audio fade-in API not available")

def _mp_audio_fade_out(audio_clip, duration):
    if hasattr(audio_clip, "audio_fadeout"):
        return audio_clip.audio_fadeout(duration)
    if afx is not None:
        return _mp_apply_effects(audio_clip, [afx.AudioFadeOut(duration)])
    raise AttributeError("MoviePy audio fade-out API not available")

def _mp_loop_audio(audio_clip, duration):
    if hasattr(audio_clip, "loop"):
        return audio_clip.loop(duration=duration)
    if afx is not None:
        return _mp_apply_effects(audio_clip, [afx.AudioLoop(duration=duration)])
    raise AttributeError("MoviePy audio loop API not available")

def _mp_write_videofile(clip, output_path, **kwargs):
    try:
        return clip.write_videofile(output_path, **kwargs)
    except TypeError as exc:
        if "unexpected keyword argument 'verbose'" not in str(exc):
            raise
        retry_kwargs = dict(kwargs)
        retry_kwargs.pop("verbose", None)
        return clip.write_videofile(output_path, **retry_kwargs)

# === Thai text helpers ===

import unicodedata

def sanitize_text(t):
    if not isinstance(t, str):
        t = str(t)
    # ลบ control chars แต่เก็บไทย
    t = "".join(ch for ch in t if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
    return t.strip()

def thai_clusters(text):
    def is_mark(ch):
        return unicodedata.category(ch) in ("Mn", "Me", "Mc") or unicodedata.combining(ch) != 0
    clusters = []
    cur = ""
    for ch in text:
        if not cur:
            cur = ch
        elif is_mark(ch):
            cur += ch
        else:
            clusters.append(cur)
            cur = ch
    if cur:
        clusters.append(cur)
    return clusters

def join_clusters(clusters):
    return "".join(clusters)

def thai_wrap_px(draw, font, text, max_px):
    """ตัดบรรทัดไทยแบบวัดพิกเซล"""
    def width(s):
        try:
            bbox = draw.textbbox((0,0), s, font=font, anchor="ls")
            return bbox[2] - bbox[0]
        except:
            return len(s) * 20
    
    clusters = thai_clusters(text)
    lines = []
    cur = ""
    for cl in clusters:
        test = cur + cl
        # ตัดที่ช่องว่างหรือคำยาว
        if width(test) > max_px and cur:
            # ลองหาจุดตัดที่ช่องว่าง
            if " " in cur:
                last_space = cur.rfind(" ")
                lines.append(cur[:last_space].strip())
                cur = cur[last_space+1:] + cl
            else:
                lines.append(cur)
                cur = cl
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines

def smart_balanced_wrap(draw, font, text, max_width, max_lines=3):
    """ตัด 3 บรรทัดให้สมดุล"""
    text = sanitize_text(text)
    # ลองตัดแบบปกติก่อน
    lines = thai_wrap_px(draw, font, text, max_width)
    if len(lines) <= max_lines:
        return lines
    
    # ถ้าเกิน 3 บรรทัด ให้บังคับตัด 3 บรรทัดโดยเฉลี่ย
    # หาจุดตัดที่สมดุล
    clusters = thai_clusters(text)
    total = len(clusters)
    per_line = math.ceil(total / max_lines)
    lines = []
    for i in range(max_lines):
        start = i * per_line
        end = min((i+1)*per_line, total)
        chunk = join_clusters(clusters[start:end])
        lines.append(chunk)
        if end >= total:
            break
    # บรรทัดสุดท้ายเก็บที่เหลือทั้งหมด
    if len(lines) == max_lines and end < total:
        lines[-1] = join_clusters(clusters[(max_lines-1)*per_line:])
    
    return lines

def fix_thai_vowel_overlap(text):
    # แก้สระลอย (placeholder - ใส่ logic เพิ่มได้)
    return text

def draw_thai_text(draw, xy, text, font, fill, anchor=None):
    try:
        draw.text(xy, text, font=font, fill=fill, anchor=anchor)
    except:
        draw.text(xy, text, font=font, fill=fill)

# === Main Renderer Class ===

class KnowledgeRenderer:
    def __init__(self, factory_settings=None):
        self.settings = factory_settings or {}
        video_cfg = self.settings.get("video", {})
        self.duration = video_cfg.get("duration", 60)
        self.volume = video_cfg.get("volume", 0.4)
        self.filter_name = video_cfg.get("filter", "Darken (Cinematic)")
        self.progress_bar = video_cfg.get("progress_bar", True)
        self.fade_in = video_cfg.get("fade_in", True)
        self.fade_out = video_cfg.get("fade_out", True)
        self.dynamic_zoom = video_cfg.get("dynamic_zoom", False)
        self.font_name = video_cfg.get("font", "NotoSansThai-Black.ttf")
        self.branding = self.settings.get("channel", {}).get("branding_text", "รู้หรือไม่? 1นาทีรู้เรื่อง")
        
    def find_font(self, font_name=None):
        """หาฟอนต์ไทย"""
        candidates = []
        if font_name:
            candidates.append(os.path.join("assets/fonts", font_name))
            candidates.append(font_name)
        candidates.extend([
            "assets/fonts/NotoSansThai-Black.ttf",
            "assets/fonts/NotoSansThai-Bold.ttf",
            "C:/Windows/Fonts/NotoSansThai-Black.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Black.ttf"
        ])
        for p in candidates:
            if os.path.exists(p):
                return p
        return None
    
    def apply_filter(self, clip, filter_name, duration):
        if filter_name == "Darken (Cinematic)":
            clip = _mp_transform_frames(clip, lambda im: np.clip(im * 0.6, 0, 255).astype('uint8'))
        elif filter_name == "Black & White":
            clip = _mp_blackwhite(clip)
        elif filter_name == "Sepia":
            matrix = np.array([[0.393, 0.769, 0.189],
                               [0.349, 0.686, 0.168],
                               [0.272, 0.534, 0.131]])
            def sepia_fl(im):
                return np.clip(im.dot(matrix.T), 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, sepia_fl)
        elif filter_name == "Warm Tone":
            def warm_fl(im):
                im = im.astype(float)
                im[:,:,0] *= 1.1
                im[:,:,2] *= 0.9
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, warm_fl)
        elif filter_name == "Cool Tone":
            def cool_fl(im):
                im = im.astype(float)
                im[:,:,0] *= 0.9
                im[:,:,2] *= 1.1
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, cool_fl)
        elif filter_name == "High Contrast":
            clip = _mp_transform_frames(clip, lambda im: np.clip(im * 1.2 - 20, 0, 255).astype('uint8'))
        elif filter_name == "Vignette":
            def vignette_fl(im):
                im = im * 0.8
                im = (im - 128) * 1.1 + 128
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, vignette_fl)
        
        if self.dynamic_zoom:
            clip = _mp_resize(clip, lambda t: 1 + (0.05 * t / duration))
            clip = _mp_set_position(clip, "center")
        if self.fade_in:
            clip = _mp_fade_in(clip, 1.0)
        if self.fade_out:
            clip = _mp_fade_out(clip, 1.0)
        return clip

    def generate_overlay(self, size, script_data, metadata, font_path):
        """
        สร้าง overlay สำหรับความรู้ 1 นาที
        เลย์เอาต์: Hook บน + เนื้อหา 3 ข้อกลาง + Branding ล่าง
        """
        w, h = size
        img = Image.new("RGBA", (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        # สีตาม pillar
        pillar_colors = {
            "Psychology": (124, 77, 255),
            "Money": (0, 200, 83),
            "Health": (255, 61, 0),
            "History": (255, 160, 0)
        }
        pillar = script_data.get("pillar", "Psychology")
        accent = pillar_colors.get(pillar, (124, 77, 255))
        
        # โหลดฟอนต์
        BODY_SIZE = 42
        HOOK_SIZE = 40
        WM_SIZE = 22
        
        font = None
        hook_font = None
        wm_font = None
        
        font_candidates = []
        if font_path and os.path.exists(font_path):
            font_candidates.append(font_path)
        # ลองหา fallback
        for fp in ["assets/fonts/NotoSansThai-Black.ttf", "assets/fonts/THSarabunNew.ttf"]:
            if os.path.exists(fp):
                font_candidates.append(fp)
        
        try:
            for cand in font_candidates:
                try:
                    font = ImageFont.truetype(cand, BODY_SIZE)
                    hook_font = ImageFont.truetype(cand, HOOK_SIZE)
                    wm_font = ImageFont.truetype(cand, WM_SIZE)
                    break
                except:
                    continue
            if font is None:
                font = ImageFont.load_default()
                hook_font = ImageFont.load_default()
                wm_font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            hook_font = ImageFont.load_default()
            wm_font = ImageFont.load_default()
        
        # ===== 1. HOOK BOX (บน 15%) =====
        hook_text = sanitize_text(script_data.get("hook", "รู้หรือไม่?"))
        show_hook = True
        hook_center_x = w / 2
        hook_center_y = h * 0.14
        pad_x, pad_y = 30, 16
        hook_box_w = int(w * 0.88)
        hook_box_h = int(h * 0.09)
        box_x1 = hook_center_x - hook_box_w/2
        box_y1 = hook_center_y - hook_box_h/2
        box_x2 = hook_x1 = box_x1 + hook_box_w
        box_y2 = hook_center_y + hook_box_h/2
        
        # สีกล่อง hook = สี accent + โปร่งนิดๆ
        box_color = accent + (230,)
        shadow_color = (0,0,0,180)
        text_color = (255,255,255,255)
        
        if show_hook and hook_text:
            # วาดกล่อง
            draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=16, fill=box_color)
            hook_max_px = hook_box_w - pad_x*2
            hook_lines = thai_wrap_px(draw, hook_font, hook_text, hook_max_px)
            if len(hook_lines) > 2:
                hook_lines = hook_lines[:2]
            
            # คำนวณความสูง
            try:
                bbox = draw.textbbox((0,0), "ที่ปู่นี้จ้ะ", font=hook_font, anchor="ls")
                line_h = bbox[3] - bbox[1]
            except:
                line_h = HOOK_SIZE
            spacing = line_h * 0.4
            total_h = line_h * len(hook_lines) + spacing * max(0, len(hook_lines)-1)
            start_y = hook_center_y - total_h/2 + line_h/2
            
            for line in hook_lines:
                line = fix_thai_vowel_overlap(line)
                # เงา
                for ox, oy in [(2,2), (-2,-2), (2,-2), (-2,2)]:
                    draw_thai_text(draw, (hook_center_x+ox, start_y+oy), line, font=hook_font, fill=shadow_color, anchor="mm")
                draw_thai_text(draw, (hook_center_x, start_y), line, font=hook_font, fill=text_color, anchor="mm")
                start_y += line_h + spacing
        
        # ===== 2. BODY BOX (กลาง 55%) - เนื้อหา 3 ข้อ =====
        # รวม point1,2,3 เป็นข้อความเดียว
        body_text = f"1. {script_data.get('point1','')}  2. {script_data.get('point2','')}  3. {script_data.get('point3','')}"
        body_text = sanitize_text(body_text)
        
        body_box_w = int(w * 0.88)
        body_box_h = int(h * 0.30)
        body_center_y = h * 0.52
        b_x1 = (w - body_box_w)/2
        b_y1 = body_center_y - body_box_h/2
        b_x2 = b_x1 + body_box_w
        b_y2 = body_center_y + body_box_h/2
        
        # กล่องดำโปร่ง
        draw.rounded_rectangle([b_x1, b_y1, b_x2, b_y2], radius=18, fill=(0,0,0,175))
        
        # ตัดคำ 3 บรรทัด
        max_line_px = body_box_w - 50
        lines = smart_balanced_wrap(draw, font, body_text, max_line_px, max_lines=3)
        
        try:
            bbox = draw.textbbox((0,0), "ที่ปู่นี้จ้ะ", font=font, anchor="ls")
            lh = bbox[3] - bbox[1]
        except:
            lh = BODY_SIZE
        ls = lh * 0.5
        total_text_h = lh * len(lines) + ls * max(0, len(lines)-1)
        
        # ถ้าเกินกล่อง ให้ลดฟอนต์
        allowed_h = body_box_h - 40
        size = BODY_SIZE
        while total_text_h > allowed_h and size > 26:
            size = int(size * 0.92)
            try:
                for cand in font_candidates:
                    try:
                        font = ImageFont.truetype(cand, size)
                        break
                    except:
                        continue
                bbox = draw.textbbox((0,0), "ที่ปู่นี้จ้ะ", font=font, anchor="ls")
                lh = bbox[3] - bbox[1]
                ls = lh * 0.5
                lines = smart_balanced_wrap(draw, font, body_text, max_line_px, max_lines=3)
                total_text_h = lh * len(lines) + ls * max(0, len(lines)-1)
            except:
                break
        
        cur_y = body_center_y - total_text_h/2 + lh/2
        for ln in lines:
            ln = fix_thai_vowel_overlap(ln)
            # เงา
            for ox, oy in [(2,2), (-2,-2), (2,-2), (-2,2), (0,3), (3,0), (-3,0)]:
                draw_thai_text(draw, (w/2+ox, cur_y+oy), ln, font=font, fill=shadow_color, anchor="mm")
            draw_thai_text(draw, (w/2, cur_y), ln, font=font, fill=text_color, anchor="mm")
            cur_y += lh + ls
        
        # ===== 3. CTA BOX (ล่าง เหนือ progress bar) =====
        cta_text = sanitize_text(script_data.get("cta", "คอมเมนต์บอกหน่อย!"))
        cta_y = h * 0.78
        cta_box_w = int(w * 0.80)
        cta_box_h = int(h * 0.07)
        c_x1 = (w - cta_box_w)/2
        c_y1 = cta_y - cta_box_h/2
        c_x2 = c_x1 + cta_box_w
        c_y2 = cta_y + cta_box_h/2
        
        # กล่อง accent อ่อน
        draw.rounded_rectangle([c_x1, c_y1, c_x2, c_y2], radius=12, fill=(255,255,255,210))
        cta_max_px = cta_box_w - 30
        cta_lines = thai_wrap_px(draw, wm_font, cta_text, cta_max_px)
        if len(cta_lines) > 1:
            cta_lines = cta_lines[:1]
            cta_lines[0] = cta_lines[0][:60] + "..." if len(cta_lines[0]) > 60 else cta_lines[0]
        try:
            bbox = draw.textbbox((0,0), cta_lines[0] if cta_lines else "test", font=wm_font, anchor="ls")
            cta_w = bbox[2]-bbox[0]
        except:
            cta_w = 200
        draw_thai_text(draw, (w/2, cta_y), cta_lines[0] if cta_lines else cta_text, font=wm_font, fill=(30,30,30,255), anchor="mm")
        
        # ===== 4. Watermark =====
        wm_y = int(h * 0.92)
        # แบ่ง branding เป็น 2 บรรทัดถ้ามี |||
        names = self.branding.split("|||")
        for name in names:
            name = name.strip()
            if not name:
                continue
            try:
                bbox = draw.textbbox((0,0), name, font=wm_font)
                tw = bbox[2]-bbox[0]
                wm_x = (w - tw)/2
                # เงา
                draw.text((wm_x+1, wm_y+1), name, font=wm_font, fill=(0,0,0,150))
                draw.text((wm_x, wm_y), name, font=wm_font, fill=(255,255,255,200))
                wm_y += 24
            except:
                pass
        
        return img

    def render(self, bg_video_path, audio_path, script_data, metadata, output_path, music_path=None):
        """
        เรนเดอร์วิดีโอ 1 ตัวเต็ม
        bg_video_path: วิดีโอพื้นหลัง
        audio_path: เสียง TTS (อาจเป็น None)
        script_data: dict hook/point1/2/3/cta
        metadata: dict title/desc
        output_path: ที่บันทึก
        music_path: เพลงประกอบ
        """
        if not MOVIEPY_AVAILABLE:
            print("[Renderer] ❌ MoviePy not installed")
            return False
        
        duration = self.duration
        # ถ้ามี audio ให้ปรับ duration ตามเสียงจริง
        if audio_path and os.path.exists(audio_path):
            try:
                tmp = AudioFileClip(audio_path)
                # บวกเผื่อ 1 วิหัวท้าย
                duration = min(62, max(45, tmp.duration + 1.5))
                tmp.close()
                print(f"[Renderer] Adjust duration to audio: {duration:.1f}s")
            except:
                pass
        
        self.duration = duration
        
        print(f"[Renderer] 🎬 Rendering {os.path.basename(output_path)} ({duration:.0f}s) filter={self.filter_name}")
        
        try:
            # 1. โหลดวิดีโอพื้นหลัง
            clip = VideoFileClip(bg_video_path)
            
            # ปรับความยาว
            if clip.duration < duration:
                loop_count = int(duration / clip.duration) + 1
                clip = _mp_subclip(_mp_loop_clip(clip, n=loop_count), 0, duration)
            else:
                start = random.uniform(0, clip.duration - duration)
                clip = _mp_subclip(clip, start, start + duration)
            
            # ครอปเป็น 9:16
            w, h = clip.size
            target_ratio = 9/16
            if w/h > target_ratio:
                new_w = h * target_ratio
                clip = _mp_crop(clip, x1=w/2 - new_w/2, x2=w/2 + new_w/2)
            
            clip = _mp_resize(clip, height=1920)
            if clip.w != 1080:
                clip = _mp_resize(clip, width=1080)
            
            clip = self.apply_filter(clip, self.filter_name, duration)
            
            # 2. เสียง
            audio_clips = []
            tts_dur = 0
            if audio_path and os.path.exists(audio_path):
                try:
                    tts_audio = AudioFileClip(audio_path)
                    # ดีเลย์ 0.5 วิก่อนพูด
                    tts_audio = _mp_set_start(tts_audio, 0.5)
                    audio_clips.append(tts_audio)
                    tts_dur = tts_audio.duration
                except Exception as e:
                    print(f"[Renderer] TTS load error: {e}")
            
            # เพลงพื้นหลัง
            if music_path and os.path.exists(music_path):
                try:
                    music_audio = AudioFileClip(music_path)
                    if music_audio.duration < duration:
                        music_audio = _mp_loop_audio(music_audio, duration)
                    else:
                        start = random.uniform(0, music_audio.duration - duration)
                        music_audio = _mp_subclip(music_audio, start, start + duration)
                    music_audio = _mp_volumex(music_audio, self.volume)
                    # ถ้ามี TTS ให้ลดเพลงลง
                    if audio_clips:
                        music_audio = _mp_volumex(music_audio, 0.35)
                    # fade
                    if self.fade_in:
                        music_audio = _mp_audio_fade_in(music_audio, 1.5)
                    if self.fade_out:
                        music_audio = _mp_audio_fade_out(music_audio, 1.5)
                    audio_clips.append(music_audio)
                except Exception as e:
                    print(f"[Renderer] Music load error: {e}")
            
            if audio_clips:
                comp_audio = CompositeAudioClip(audio_clips)
                # ตัดให้เท่ากับ duration
                if comp_audio.duration > duration:
                    comp_audio = _mp_subclip(comp_audio, 0, duration)
                clip = _mp_set_audio(clip, comp_audio)
            
            # 3. Overlay ข้อความ
            ref_frame = clip.get_frame(0)
            font_path = self.find_font(self.font_name)
            overlay_img = self.generate_overlay(clip.size, script_data, metadata, font_path)
            txt_clip = _mp_set_duration(ImageClip(np.array(overlay_img)), duration)
            if self.fade_in:
                txt_clip = _mp_fade_in(txt_clip, 0.8)
            if self.fade_out:
                txt_clip = _mp_fade_out(txt_clip, 0.8)
            
            layers = [clip, txt_clip]
            
            # 4. Progress bar
            if self.progress_bar:
                bar_h = 8
                bar_color = (255, 200, 0)  # เหลืองทอง
                prog_bar_bg = _mp_set_duration(ColorClip(size=(1080, bar_h), color=(255,255,255)), duration)
                prog_bar_bg = _mp_set_position(prog_bar_bg, ('center', 1920-bar_h))
                prog_bar_bg = _mp_set_duration(prog_bar_bg, duration)
                # ทำ progress bar แบบเคลื่อนที่ (ใช้ mask ไม่ได้ง่าย เลยทำแบบ static ก่อน)
                # ง่ายๆ: ทำแถบสีที่ขยายตามเวลา - ใช้ resize แบบ function
                # แต่เพื่อความง่าย ทำแถบเต็ม แล้ว fade in แบบ wipe - ข้ามไปก่อน
                # ทำแบบง่าย: แถบบางๆ ด้านล่าง
                bar = _mp_set_duration(ColorClip(size=(1080, bar_h), color=bar_color), duration)
                bar = _mp_set_position(bar, ('center', 1920-bar_h))
                layers.append(prog_bar_bg)
                layers.append(bar)
            
            final = CompositeVideoClip(layers, size=(1080, 1920))
            
            # 5. เขียนไฟล์
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            _mp_write_videofile(
                final,
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                preset='ultrafast',
                ffmpeg_params=['-crf', '23'],
                logger=None
            )
            
            # ปิด clip
            try:
                clip.close()
                final.close()
                if audio_clips:
                    for ac in audio_clips:
                        try: ac.close()
                        except: pass
            except:
                pass
            
            print(f"[Renderer] ✅ Done: {output_path}")
            return True
            
        except Exception as e:
            import traceback
            print(f"[Renderer] ❌ Render error: {e}")
            traceback.print_exc()
            return False
