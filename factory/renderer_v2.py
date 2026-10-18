"""
renderer_v2.py - เรนเดอร์วิดีโอ 9:16 ที่แก้ไขแล้ว
- ฟอนต์ไทยถูกต้อง
- เลย์เอาต์ใหม่ชัดเจน
- เสียงดี
"""
import os
import random
import re
import math
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageStat
from datetime import datetime

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

# ========== MoviePy helpers ==========

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

# ========== Thai text helpers (แบบง่ายและถูกต้อง) ==========

import unicodedata

def sanitize_text(t):
    if not isinstance(t, str):
        t = str(t)
    # ลบ control chars ที่อาจทำให้ render พัง
    t = "".join(ch for ch in t if unicodedata.category(ch)[0] != "C" or ch in "\n\t ")
    # ลบ zero-width
    t = t.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    return t.strip()

def find_thai_font():
    """หาฟอนต์ไทยที่ใช้งานได้จริง"""
    candidates = [
        os.path.abspath("assets/fonts/NotoSansThai-Black.ttf"),
        os.path.abspath("assets/fonts/NotoSansThai-Variable.ttf"),
        "assets/fonts/NotoSansThai-Black.ttf",
        "assets/fonts/NotoSansThai-Variable.ttf",
        "C:/Windows/Fonts/NotoSansThai-Black.ttf",
        "C:/Windows/Fonts/THSarabunNew.ttf",
        "C:/Windows/Fonts/THSarabun.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Black.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                # ทดสอบโหลด
                test = ImageFont.truetype(p, 20)
                # ทดสอบ render ไทย
                img = Image.new("RGB", (100, 50))
                d = ImageDraw.Draw(img)
                d.text((10,10), "ทดสอบ", font=test, fill=(255,255,255))
                print(f"[Font] ✅ Found: {p}")
                return p
            except Exception as e:
                print(f"[Font] ❌ Failed {p}: {e}")
                continue
    print("[Font] ⚠️ No Thai font found, fallback to default (may show squares)")
    return None

def wrap_text_by_width(draw, font, text, max_width):
    """ตัดบรรทัดตามความกว้างพิกเซล แบบง่าย ไม่ใช้ clusters ซับซ้อน"""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        try:
            bbox = draw.textbbox((0,0), test, font=font)
            w = bbox[2] - bbox[0]
        except:
            w = len(test) * 20
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            # ถ้าคำเดียวก็ยาวเกิน ให้ตัดคำนั้นตรงๆ (ไม่สวยแต่ไม่หาย)
            try:
                bbox2 = draw.textbbox((0,0), current, font=font)
                if bbox2[2] - bbox2[0] > max_width:
                    # ตัดคำยาว
                    cut = ""
                    for ch in current:
                        test_cut = cut + ch
                        bb = draw.textbbox((0,0), test_cut, font=font)
                        if bb[2] - bb[0] > max_width:
                            lines.append(cut)
                            cut = ch
                        else:
                            cut = test_cut
                    current = cut
            except:
                pass
    if current:
        lines.append(current)
    return lines

# ========== Renderer ==========

class KnowledgeRendererV2:
    def __init__(self, factory_settings=None):
        self.settings = factory_settings or {}
        video_cfg = self.settings.get("video", {})
        self.duration = video_cfg.get("duration", 60)
        self.volume = video_cfg.get("volume", 0.35)  # ลดลงจาก 0.4 -> 0.35 เพื่อไม่กลบเสียงพูด
        self.filter_name = video_cfg.get("filter", "Darken (Cinematic)")
        self.progress_bar = video_cfg.get("progress_bar", True)
        self.fade_in = video_cfg.get("fade_in", True)
        self.fade_out = video_cfg.get("fade_out", True)
        self.dynamic_zoom = video_cfg.get("dynamic_zoom", False)
        self.font_path = find_thai_font()
        if not self.font_path:
            # Fallback to specified font name
            self.font_path = video_cfg.get("font", "NotoSansThai-Black.ttf")
        self.branding = self.settings.get("channel", {}).get("branding_text", "รู้หรือไม่? 1นาทีรู้เรื่อง")
        print(f"[RendererV2] Font: {self.font_path}, Duration: {self.duration}s")

    def apply_filter(self, clip, filter_name, duration):
        if filter_name == "Darken (Cinematic)":
            clip = _mp_transform_frames(clip, lambda im: np.clip(im * 0.62, 0, 255).astype('uint8'))
        elif filter_name == "Black & White":
            clip = _mp_blackwhite(clip)
        elif filter_name == "Sepia":
            matrix = np.array([[0.393, 0.769, 0.189],[0.349, 0.686, 0.168],[0.272, 0.534, 0.131]])
            def sepia_fl(im):
                return np.clip(im.dot(matrix.T), 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, sepia_fl)
        elif filter_name == "Warm Tone":
            def warm_fl(im):
                im = im.astype(float); im[:,:,0] *= 1.1; im[:,:,2] *= 0.9
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, warm_fl)
        elif filter_name == "Cool Tone":
            def cool_fl(im):
                im = im.astype(float); im[:,:,0] *= 0.9; im[:,:,2] *= 1.1
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, cool_fl)
        if self.dynamic_zoom:
            clip = _mp_resize(clip, lambda t: 1 + (0.04 * t / duration))
            clip = _mp_set_position(clip, "center")
        if self.fade_in:
            clip = _mp_fade_in(clip, 0.8)
        if self.fade_out:
            clip = _mp_fade_out(clip, 0.8)
        return clip

    def generate_overlay(self, size, script_data, metadata):
        w, h = size
        img = Image.new("RGBA", (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        # สี accent ตามหมวด
        pillar_colors = {
            "Psychology": (124, 77, 255),
            "Money": (0, 200, 83),
            "Health": (255, 61, 0),
            "History": (255, 160, 0)
        }
        pillar = script_data.get("pillar", "Psychology")
        accent = pillar_colors.get(pillar, (124, 77, 255))

        # ขนาดฟอนต์ที่เหมาะสมสำหรับ 1080x1920
        HOOK_SIZE = 44  # ใหญ่ขึ้นเล็กน้อย
        BODY_SIZE = 38  # ปรับให้อ่านง่าย
        CTA_SIZE = 26
        NUM_SIZE = 32
        BRAND_SIZE = 22

        # โหลดฟอนต์
        def load_font(size):
            # ลอง variable font ก่อน (มีน้ำหนักหลายแบบ)
            for path in [self.font_path, "assets/fonts/NotoSansThai-Black.ttf", "assets/fonts/NotoSansThai-Variable.ttf"]:
                if path and os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except:
                        continue
            return ImageFont.load_default()

        hook_font = load_font(HOOK_SIZE)
        body_font = load_font(BODY_SIZE)
        cta_font = load_font(CTA_SIZE)
        num_font = load_font(NUM_SIZE)
        brand_font = load_font(BRAND_SIZE)

        # ===== 1. HOOK BOX (บน) =====
        hook_text = sanitize_text(script_data.get("hook", "รู้หรือไม่?"))
        if hook_text:
            pad_x, pad_y = 40, 24
            hook_center_y = h * 0.12
            max_w = int(w * 0.88) - pad_x*2
            hook_lines = wrap_text_by_width(draw, hook_font, hook_text, max_w)
            if len(hook_lines) > 2:
                hook_lines = hook_lines[:2]

            # คำนวณขนาดกล่อง
            try:
                bbox = draw.textbbox((0,0), "ก", font=hook_font)
                line_h = bbox[3] - bbox[1]
            except:
                line_h = HOOK_SIZE + 8
            line_spacing = int(line_h * 0.35)
            total_h = len(hook_lines) * line_h + (len(hook_lines)-1) * line_spacing
            box_h = total_h + pad_y*2 + 12
            box_w = int(w * 0.90)
            box_x1 = (w - box_w)//2
            box_y1 = int(hook_center_y - box_h//2)
            box_x2 = box_x1 + box_w
            box_y2 = box_y1 + box_h

            # วาดกล่องม่วง
            draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=20, fill=accent + (255,))

            # วาดข้อความ hook (กลางกล่อง)
            y = box_y1 + pad_y + line_h//2 + 4
            for line in hook_lines:
                # เงา
                draw.text((w//2+3, y+3), line, font=hook_font, fill=(0,0,0,120), anchor="mm")
                draw.text((w//2, y), line, font=hook_font, fill=(255,255,255,255), anchor="mm")
                y += line_h + line_spacing

        # ===== 2. BODY BOX (กลาง) - 3 ข้อ =====
        body_box_w = int(w * 0.92)
        body_box_h = int(h * 0.42)
        body_center_y = h * 0.50
        b_x1 = (w - body_box_w)//2
        b_y1 = int(body_center_y - body_box_h//2)
        b_x2 = b_x1 + body_box_w
        b_y2 = b_y1 + body_box_h

        # กล่องดำโปร่ง
        draw.rounded_rectangle([b_x1, b_y1, b_x2, b_y2], radius=22, fill=(0,0,0,175))

        # เตรียม 3 points
        points = [
            sanitize_text(script_data.get("point1", "")),
            sanitize_text(script_data.get("point2", "")),
            sanitize_text(script_data.get("point3", "")),
        ]
        # กรองที่ว่าง
        points = [p for p in points if p.strip()]
        if not points:
            # fallback จาก full_script
            full = sanitize_text(script_data.get("full_script", ""))[:120]
            points = [full]

        # วาดแต่ละ point
        pad_inner = 36
        content_w = body_box_w - pad_inner*2 - 62  # เว้นที่ให้เลข 1. 2. 3.
        try:
            bbox = draw.textbbox((0,0), "ก", font=body_font)
            lh = bbox[3] - bbox[1]
        except:
            lh = BODY_SIZE + 6
        ls = int(lh * 0.42)

        # จัดให้อยู่กลางกล่อง
        # คำนวณความสูงรวมก่อน
        all_lines = []
        for idx, pt in enumerate(points):
            # ใส่เลขข้อไว้ข้างหน้า
            prefixed = f"{pt}"
            lines = wrap_text_by_width(draw, body_font, prefixed, content_w)
            # จำกัดไม่ให้แต่ละข้อเกิน 2 บรรทัด
            if len(lines) > 2:
                lines = lines[:2]
                if len(lines[-1]) > 50:
                    lines[-1] = lines[-1][:48] + "..."
            all_lines.append((idx, lines))

        total_text_h = 0
        for idx, lines in all_lines:
            total_text_h += lh * len(lines) + ls * (len(lines)-1)
            if idx < len(all_lines)-1:
                total_text_h += 26  # ช่องว่างระหว่างข้อเพิ่มขึ้น

        start_y = int(body_center_y - total_text_h//2 + lh//2)

        for idx, lines in all_lines:
            # คำนวณ y กึ่งกลางของ block นี้เพื่อวางเลข
            block_h = lh * len(lines) + ls * (len(lines)-1)
            block_center_y = start_y + block_h//2 - lh//2

            # วาดเลขข้อวงกลม (กลาง block)
            num_text = str(idx+1)
            num_cx = b_x1 + pad_inner + 24
            num_cy = block_center_y + 6
            r = 20
            draw.ellipse([num_cx-r, num_cy-r, num_cx+r, num_cy+r], fill=accent + (255,))
            # ปรับตำแหน่งเลขให้อยู่กลางวงกลมจริงๆ
            try:
                nb = draw.textbbox((0,0), num_text, font=num_font, anchor="mm")
                # ใช้ anchor mm จะกลางพอดี
            except:
                pass
            draw.text((num_cx, num_cy+2), num_text, font=num_font, fill=(255,255,255,255), anchor="mm")

            # วาดข้อความแต่ละบรรทัดของข้อนี้
            text_x = b_x1 + pad_inner + 56
            for line_idx, line in enumerate(lines):
                # เงา
                draw.text((text_x+2, start_y+2), line, font=body_font, fill=(0,0,0,170), anchor="lm")
                draw.text((text_x, start_y), line, font=body_font, fill=(255,255,255,255), anchor="lm")
                start_y += lh + ls
            if idx < len(all_lines)-1:
                start_y += 26 + lh//2 - lh//2
                # ลบ ls ส่วนเกิน
                start_y -= ls
                start_y += 8

        # ===== 3. CTA BOX (ล่าง) =====
        cta_text = sanitize_text(script_data.get("cta", "คอมเมนต์บอกหน่อย!"))
        if cta_text:
            cta_pad_x, cta_pad_y = 30, 18
            max_cta_w = int(w * 0.84) - cta_pad_x*2
            cta_lines = wrap_text_by_width(draw, cta_font, cta_text, max_cta_w)
            if len(cta_lines) > 1:
                cta_lines = cta_lines[:1]
                if len(cta_lines[0]) > 55:
                    cta_lines[0] = cta_lines[0][:52] + "..."
            try:
                bbox = draw.textbbox((0,0), cta_lines[0], font=cta_font)
                cta_line_h = bbox[3] - bbox[1]
            except:
                cta_line_h = CTA_SIZE
            cta_box_h = cta_line_h + cta_pad_y*2 + 10
            cta_box_w = int(w * 0.86)
            cta_y = h * 0.82
            c_x1 = (w - cta_box_w)//2
            c_y1 = int(cta_y - cta_box_h//2)
            c_x2 = c_x1 + cta_box_w
            c_y2 = c_y1 + cta_box_h

            draw.rounded_rectangle([c_x1, c_y1, c_x2, c_y2], radius=16, fill=(255,255,255,240))

            cy = cta_y
            for line in cta_lines:
                draw.text((w//2, cy), line, font=cta_font, fill=(30,30,30,255), anchor="mm")

        # ===== 4. Branding (ล่างสุด) =====
        brand_y = int(h * 0.94)
        brand_text = sanitize_text(self.branding)
        if brand_text:
            # วาดแบบกลาง
            draw.text((w//2+1, brand_y+1), brand_text, font=brand_font, fill=(0,0,0,140), anchor="mm")
            draw.text((w//2, brand_y), brand_text, font=brand_font, fill=(255,255,255,190), anchor="mm")

        return img

    def render(self, bg_video_path, audio_path, script_data, metadata, output_path, music_path=None):
        if not MOVIEPY_AVAILABLE:
            print("[RendererV2] ❌ MoviePy not installed")
            return False

        duration = self.duration
        # ปรับ duration ตามเสียงจริงถ้ามี
        if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            try:
                tmp = AudioFileClip(audio_path)
                duration = min(62, max(20, tmp.duration + 2.5))
                tmp.close()
                print(f"[RendererV2] Adjust duration to audio: {duration:.1f}s")
            except:
                pass
        self.duration = duration
        print(f"[RendererV2] 🎬 Rendering {os.path.basename(output_path)} ({duration:.0f}s) filter={self.filter_name}")

        try:
            clip = VideoFileClip(bg_video_path)
            if clip.duration < duration:
                loop_count = int(duration / clip.duration) + 1
                clip = _mp_subclip(_mp_loop_clip(clip, n=loop_count), 0, duration)
            else:
                start = random.uniform(0, max(0, clip.duration - duration))
                clip = _mp_subclip(clip, start, start + duration)
            w, h = clip.size
            target_ratio = 9/16
            if w/h > target_ratio:
                new_w = h * target_ratio
                clip = _mp_crop(clip, x1=w/2 - new_w/2, x2=w/2 + new_w/2)
            clip = _mp_resize(clip, height=1920)
            if clip.w != 1080:
                clip = _mp_resize(clip, width=1080)
            clip = self.apply_filter(clip, self.filter_name, duration)

            # Audio
            audio_clips = []
            if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                try:
                    tts_audio = AudioFileClip(audio_path)
                    tts_audio = _mp_set_start(tts_audio, 0.6)
                    audio_clips.append(tts_audio)
                    print(f"[RendererV2] TTS: {tts_audio.duration:.1f}s")
                except Exception as e:
                    print(f"[RendererV2] TTS load error: {e}")
            else:
                print("[RendererV2] No TTS audio, music only")

            if music_path and os.path.exists(music_path):
                try:
                    music_audio = AudioFileClip(music_path)
                    if music_audio.duration < duration:
                        music_audio = _mp_loop_audio(music_audio, duration)
                    else:
                        start = random.uniform(0, music_audio.duration - duration)
                        music_audio = _mp_subclip(music_audio, start, start + duration)
                    # ปรับ volume: ถ้ามี TTS ให้เบาลง
                    if audio_clips:
                        music_audio = _mp_volumex(music_audio, 0.22)  # เบามากเมื่อมีเสียงพูด
                    else:
                        music_audio = _mp_volumex(music_audio, 0.38)  # ดังพอดีเมื่อไม่มีเสียงพูด
                    if self.fade_in:
                        music_audio = _mp_audio_fade_in(music_audio, 1.0)
                    if self.fade_out:
                        music_audio = _mp_audio_fade_out(music_audio, 1.0)
                    audio_clips.append(music_audio)
                    print(f"[RendererV2] Music: {os.path.basename(music_path)} vol={'0.22' if len(audio_clips)>1 else '0.38'}")
                except Exception as e:
                    print(f"[RendererV2] Music error: {e}")

            if audio_clips:
                comp_audio = CompositeAudioClip(audio_clips)
                if comp_audio.duration > duration:
                    comp_audio = _mp_subclip(comp_audio, 0, duration)
                clip = _mp_set_audio(clip, comp_audio)
            else:
                print("[RendererV2] ⚠️ No audio at all - video will be silent")

            # Overlay
            overlay_img = self.generate_overlay(clip.size, script_data, metadata)
            txt_clip = _mp_set_duration(ImageClip(np.array(overlay_img)), duration)
            if self.fade_in:
                txt_clip = _mp_fade_in(txt_clip, 0.6)
            if self.fade_out:
                txt_clip = _mp_fade_out(txt_clip, 0.6)

            layers = [clip, txt_clip]
            if self.progress_bar:
                bar_h = 6
                bar_bg = _mp_set_duration(ColorClip(size=(1080, bar_h), color=(255,255,255)), duration)
                bar_bg = _mp_set_position(bar_bg, ('center', 1920-bar_h))
                layers.append(bar_bg)
                # ทำ progress bar แบบ full (simplified)
                bar = _mp_set_duration(ColorClip(size=(1080, bar_h), color=(255,200,0)), duration)
                bar = _mp_set_position(bar, ('center', 1920-bar_h))
                layers.append(bar)

            final = CompositeVideoClip(layers, size=(1080, 1920))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            _mp_write_videofile(final, output_path, fps=30, codec='libx264', audio_codec='aac', threads=4, preset='ultrafast', ffmpeg_params=['-crf', '23'], logger=None)
            try:
                clip.close(); final.close()
                for ac in audio_clips:
                    try: ac.close()
                    except: pass
            except:
                pass
            print(f"[RendererV2] ✅ Done: {output_path} ({os.path.getsize(output_path)//1024} KB)")
            return True
        except Exception as e:
            import traceback
            print(f"[RendererV2] ❌ Error: {e}")
            traceback.print_exc()
            return False
