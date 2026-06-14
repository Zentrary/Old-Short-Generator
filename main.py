import os
import re
import random
import threading
import textwrap
import json
import time
import shutil
import requests
import webbrowser
import io
import subprocess
import imageio
import asyncio
import edge_tts
import warnings
import cloudscraper
import heapq
import calendar

from tkinter import messagebox
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

                                   
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module='pygame')
warnings.filterwarnings("ignore", category=UserWarning, message='.*pkg_resources.*')

from groq import Groq
from datetime import datetime, timedelta
import customtkinter as ctk
from PIL import Image, ImageFont, ImageDraw, ImageStat, ImageTk, ImageEnhance
import numpy as np
import unicodedata
import math
from bs4 import BeautifulSoup
import pygame

                               
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

vfx = None
afx = None

try:
    try:
        from moviepy.editor import (
            VideoFileClip,
            AudioFileClip,
            CompositeVideoClip,
            ImageClip,
            ColorClip,
            CompositeAudioClip,
            vfx,
        )
        afx = None
    except ImportError:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
            CompositeVideoClip,
            ImageClip,
            ColorClip,
            CompositeAudioClip,
            vfx,
            afx,
        )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from customtkinter import filedialog

                           
ASSETS_DIR = "assets"
DIRS = {
    "backgrounds": os.path.join(ASSETS_DIR, "backgrounds"),
    "music": os.path.join(ASSETS_DIR, "music"),
    "fonts": os.path.join(ASSETS_DIR, "fonts"),
    "quotes": "config/quotes.json",
    "hooks": "config/hooks.json",
    "history": "config/history.json",
    "output": "outputs",
    "config": "config/settings.json"
}

                         
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


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
        if n is not None:
            kwargs["n"] = n
        if duration is not None:
            kwargs["duration"] = duration
        return clip.loop(**kwargs)

    effect_kwargs = {}
    if n is not None:
        effect_kwargs["n"] = n
    if duration is not None:
        effect_kwargs["duration"] = duration
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


def _parse_duration_seconds(value, default=15):
    if isinstance(value, (int, float)):
        return max(1, int(value))

    if value is None:
        return default

    match = re.search(r"\d+", str(value))
    if not match:
        return default

    try:
        return max(1, int(match.group()))
    except (TypeError, ValueError):
        return default


def _mp_write_videofile(clip, output_path, **kwargs):
    try:
        return clip.write_videofile(output_path, **kwargs)
    except TypeError as exc:
        if "unexpected keyword argument 'verbose'" not in str(exc):
            raise

        retry_kwargs = dict(kwargs)
        retry_kwargs.pop("verbose", None)
        return clip.write_videofile(output_path, **retry_kwargs)
                                                                        
class VideoPlayerFrame(ctk.CTkFrame):
    def __init__(self, parent, width=270, height=480):
        super().__init__(parent, width=width, height=height, fg_color="#000", corner_radius=10)
        self.pack_propagate(False)
        self.label = ctk.CTkLabel(self, text="▶ Preview Player", text_color="gray")
        self.label.pack(fill="both", expand=True)
        self.reader = None
        self.running = False
        self.thread = None
        self.current_file = None
        self.current_image_ref = None

    def load_video(self, path):
        self.stop()
        self.current_file = path
        try:
            try:
                self.label.configure(text="Loading...", image=None)
            except Exception:
                self.label.destroy()
                self.label = ctk.CTkLabel(self, text="Loading...", text_color="gray")
                self.label.pack(fill="both", expand=True)
        except:
            pass
            
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            if os.path.getsize(path) < 1000:
                raise ValueError("File is too small, likely corrupted.")

            self.reader = imageio.get_reader(path)
            self.meta = self.reader.get_meta_data()
            self.fps = self.meta.get('fps', 30)

            self.running = True
            self.thread = threading.Thread(target=self.play_loop)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            err_msg = f"Error: {str(e)[:50]}..."
            try:
                self.label.configure(text=err_msg, image=None)
            except:
                pass
            pass

    def play_loop(self):
        reader = self.reader
        try:
            target_h = 480
            try:
                target_h = self.winfo_height()
            except: pass
            
            if target_h < 100: target_h = 480

            for frame in reader:
                if not self.running: break
                if self.reader != reader: break
                img = Image.fromarray(frame)
                w, h = img.size
                scale = target_h / h
                new_w = int(w * scale)
                new_h = target_h
                
                img = img.resize((new_w, new_h), Image.Resampling.NEAREST)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                self.after(0, self.update_image, ctk_img)
                time.sleep(1/self.fps)

            if self.running and self.reader == reader:
                self.after(0, lambda: self.load_video(self.current_file))

        except Exception as e:
            if "generator already executing" not in str(e):
                pass
        finally:
            try:
                reader.close()
            except: pass

    def update_image(self, img):
        if self.running:
            self.current_image_ref = img
            try:
                self.label.configure(image=img, text="")
            except: pass

    def stop(self):
        self.running = False

    def clear(self, message="▶ Preview Player"):
        self.stop()
        try:
            self.label.configure(image=None, text=message)
        except Exception:
            try:
                self.label.destroy()
                self.label = ctk.CTkLabel(self, text=message, text_color="gray")
                self.label.pack(fill="both", expand=True)
            except:
                pass
                                                                         
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings_ref, save_callback):
        super().__init__(parent)
        self.title("⚙️ Advanced Settings")
        self.geometry("500x600")
        self.settings = settings_ref
        self.save_cb = save_callback

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_ui = self.tabview.add("Interface")
        self.tab_gen = self.tabview.add("Generator")
        self.tab_audio = self.tabview.add("Audio/TTS")
        self.tab_visual = self.tabview.add("Visual")
        self.tab_ai = self.tabview.add("AI Writer")

        ctk.CTkLabel(self.tab_ui, text="Theme Color", font=("bold", 14)).pack(pady=10)
        self.combo_theme = ctk.CTkOptionMenu(self.tab_ui, values=["blue", "green", "dark-blue"])
        self.combo_theme.pack()

        ctk.CTkLabel(self.tab_gen, text="Default Duration", font=("bold", 14)).pack(pady=10)
        self.entry_dur = ctk.CTkEntry(self.tab_gen)
        self.entry_dur.pack()
        self.entry_dur.insert(0, str(self.settings.get("duration", 15)))

        ctk.CTkLabel(self.tab_gen, text="API Keys (Pexels/Pixabay)", font=("bold", 14)).pack(pady=10)
        self.entry_pex = ctk.CTkEntry(self.tab_gen, placeholder_text="Pexels Key")
        self.entry_pex.pack(fill="x", padx=20, pady=5)
        self.entry_pex.insert(0, self.settings.get("pexels_key", ""))

        self.entry_pix = ctk.CTkEntry(self.tab_gen, placeholder_text="Pixabay Key")
        self.entry_pix.pack(fill="x", padx=20, pady=5)
        self.entry_pix.insert(0, self.settings.get("pixabay_key", ""))

        ctk.CTkLabel(self.tab_audio, text="AI Text-to-Speech TTS (DEMO)", font=("bold", 14)).pack(pady=10)
        self.var_tts = ctk.BooleanVar(value=self.settings.get("tts_enabled", False))
        ctk.CTkCheckBox(self.tab_audio, text="Enable TTS", variable=self.var_tts).pack(pady=5)

        ctk.CTkLabel(self.tab_audio, text="Voice Selection", font=("bold", 12)).pack(pady=(10, 5))
        self.combo_voice = ctk.CTkOptionMenu(self.tab_audio, values=[
            "th-TH-NiwatNeural", "th-TH-PremwadeeNeural", 
            "en-US-AndrewNeural", "en-US-AvaNeural"
        ])
        self.combo_voice.pack()
        self.combo_voice.set(self.settings.get("tts_voice", "th-TH-NiwatNeural"))

        ctk.CTkLabel(self.tab_visual, text="Text Readability", font=("bold", 14)).pack(pady=10)
        self.var_backdrop = ctk.BooleanVar(value=self.settings.get("text_backdrop", False))
        ctk.CTkCheckBox(self.tab_visual, text="Enable Text Backdrop (Box)", variable=self.var_backdrop).pack(pady=5)

        ctk.CTkLabel(self.tab_visual, text="Backdrop Opacity (0.0 - 1.0)", font=("bold", 12)).pack(pady=(10, 5))
        self.slider_opacity = ctk.CTkSlider(self.tab_visual, from_=0.0, to=1.0, number_of_steps=10)
        self.slider_opacity.pack(pady=5)
        self.slider_opacity.set(self.settings.get("backdrop_opacity", 0.4))

        ctk.CTkLabel(self.tab_ai, text="Groq AI (Free Llama 3)", font=("bold", 14)).pack(pady=10)
        ctk.CTkLabel(self.tab_ai, text="Get free key at: console.groq.com", text_color="gray").pack()
        
        self.entry_groq = ctk.CTkEntry(self.tab_ai, placeholder_text="gsk_...")
        self.entry_groq.pack(fill="x", padx=20, pady=10)
        self.entry_groq.insert(0, self.settings.get("groq_api_key", ""))

        ctk.CTkButton(self, text="Save & Close", command=self.save_and_close, fg_color="green").pack(pady=10)

    def save_and_close(self):
        self.settings["duration"] = self.entry_dur.get()
        self.settings["pexels_key"] = self.entry_pex.get()
        self.settings["pixabay_key"] = self.entry_pix.get()
        self.settings["tts_enabled"] = self.var_tts.get()
        self.settings["tts_voice"] = self.combo_voice.get()
        self.settings["text_backdrop"] = self.var_backdrop.get()
        self.settings["backdrop_opacity"] = self.slider_opacity.get()
        self.settings["groq_api_key"] = self.entry_groq.get()
        self.save_cb()
        self.destroy()
                                                                            
class SocialMediaAutomator:
    def __init__(self, log_callback, headless=False):
        self.log = log_callback
        self.headless = headless
        self.driver = None
        self.windows = {}

    def start_browser(self):
        if not SELENIUM_AVAILABLE:
            self.log("Error: Selenium not installed.")
            return False

        try:
            options = webdriver.ChromeOptions()

            user_data_dir = os.path.abspath("chrome_data")
            options.add_argument(f"user-data-dir={user_data_dir}")

            if self.headless:
                options.add_argument("--headless=new")

            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")

            self.log("Launching Bot Chrome...")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            return True

        except Exception as e:
            self.log(f"❌ Browser Launch Failed: {e}")
            return False

    def get_url(self, platform):
        if platform == "TikTok": return "https://www.tiktok.com/upload"
        if platform == "Instagram": return "https://www.instagram.com/"
        if platform == "Shorts": return "https://studio.youtube.com/"
        if platform == "Facebook": return "https://www.facebook.com/reels/create"
        return "about:blank"

    def check_login_needed(self, platform):
        try:
            url = self.driver.current_url.lower()
            if platform == "TikTok":
                return "login" in url or "signup" in url
            if platform == "Instagram":
                return "accounts/login" in url or "login" in url
            if platform == "Shorts":
                return "accounts.google.com" in url or "signin" in url
            if platform == "Facebook":
                return "facebook.com/login" in url or "login" in url and "facebook" in url
            return False
        except:
            return False

    def prepare_sessions(self, platforms):
        self.log("Preparing browsers for selected platforms...")
        self.windows = {}

        if not self.driver:
            return False

        try:
            main_handle = self.driver.current_window_handle
        except:
            self.log("Error: Browser closed.")
            return False

        for i, platform in enumerate(platforms):
            target_url = self.get_url(platform)

            if i == 0:

                self.driver.switch_to.window(main_handle)
                self.windows[platform] = main_handle
            else:

                self.driver.execute_script("window.open('about:blank', '_blank');")

                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.windows[platform] = self.driver.current_window_handle

            self.driver.get(target_url)
            self.log(f"Opened window for {platform}...")
            time.sleep(3)

            if self.check_login_needed(platform):
                self.log(f"⚠ LOGIN REQUIRED for {platform}!")
                self.log(f"Please login manually in the {platform} window now.")
                self.log("Waiting for login completion...")

                start_time = time.time()
                while self.check_login_needed(platform):
                    if time.time() - start_time > 300:
                        self.log(f"❌ Login Timeout for {platform}. Skipping.")
                        break
                    time.sleep(2)

                    try:
                        _ = self.driver.title
                    except:
                        return False

                if not self.check_login_needed(platform):
                    self.log(f"✅ Login detected for {platform}!")

                    if platform == "TikTok" and "upload" not in self.driver.current_url:
                        self.driver.get(target_url)

        return True

    def upload_tiktok(self, file_path, caption):
        if "TikTok" not in self.windows: return "Window not found"
        try:
            self.driver.switch_to.window(self.windows["TikTok"])
        except:
            return "Browser Window Closed"

        try:
            if "upload" not in self.driver.current_url:
                self.driver.get("https://www.tiktok.com/upload")
                time.sleep(3)

            if "login" in self.driver.current_url:
                self.log("⚠ TikTok Login Required!")
                return "Manual Login Required"

            try:
                file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                file_input.send_keys(file_path)
                self.log("TikTok: File uploaded.")
            except:
                self.log("TikTok: Could not auto-upload file. Please select manually.")

            try:
                time.sleep(2)

                caption_area = None

                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                    )
                    caption_area = self.driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                except:

                    try:
                        caption_area = self.driver.find_element(By.XPATH, "//div[contains(@class, 'public-DraftEditor-content')]")
                    except:
                        pass

                if caption_area:
                    caption_area.click()
                    time.sleep(1)
                    caption_area.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    caption_area.send_keys(Keys.DELETE)
                    time.sleep(0.5)

                    import pyperclip
                    pyperclip.copy(caption)
                    time.sleep(0.5)
                    caption_area.send_keys(Keys.CONTROL, 'v')
                    time.sleep(1)

                    self.log("TikTok: Caption filled (via Paste).")
                else:
                    self.log("TikTok: Caption area not found.")

            except Exception as e:
                self.log(f"TikTok: Caption Error: {e}")

            try:
                time.sleep(2)
                turn_on_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Turn on')]")
                if turn_on_btn:
                    self.log("ℹ Found popup. Clicking 'Turn on'...")
                    turn_on_btn[0].click()
            except:
                pass

            self.log("⏳ Waiting for TikTok checks (Copyright/Content)...")
            check_wait_start = time.time()
            checks_passed = False

            while time.time() - check_wait_start < 600:
                if not self.driver: break
                try:

                    checking_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Checking in progress')]")
                    still_checking = False
                    for el in checking_indicators:
                        if el.is_displayed():
                            still_checking = True
                            break

                    if still_checking:
                        if int(time.time()) % 5 == 0:
                            self.log("... Checks still running ...")
                        time.sleep(2)
                        continue

                    issues_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Copyright claim found')]")
                    issue_found = False
                    for el in issues_indicators:
                        if el.is_displayed():
                            self.log("⚠ Warning: Copyright claim detected!")
                            issue_found = True
                            break
                    if issue_found:
                         break

                    self.log("✅ Checks appear complete!")
                    checks_passed = True
                    time.sleep(2)
                    break
                except:
                    time.sleep(2)

            if not checks_passed:
                self.log("⚠ Wait time exceeded or checks unclear. Attempting to post anyway...")

            try:
                time.sleep(2)
                self.log("Attempting to click Post...")

                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(1)
                except:
                    pass

                post_btn = None
                selectors = [
                    "//button[contains(., 'Post')]",
                    "//button[contains(., 'POST')]",
                    "//div[contains(text(), 'Post')]",
                    "//div[contains(text(), 'POST')]",
                    "//button[.//div[contains(text(), 'Post')]]",
                    "//button[.//div[contains(text(), 'POST')]]",
                    "//div[contains(@class, 'btn-post')]"
                ]

                for xpath in selectors:
                    try:
                        btn_candidates = self.driver.find_elements(By.XPATH, xpath)
                        for btn in btn_candidates:
                            if btn.is_displayed() and btn.is_enabled():

                                data_tt = btn.get_attribute("data-tt")
                                if data_tt and "Sidebar" in data_tt:
                                    continue

                                post_btn = btn
                                self.log(f"Found Post button with: {xpath}")
                                break
                        if post_btn: break
                    except:
                        continue

                if not post_btn:

                    try:
                        post_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'Button__root--type-primary')]")
                        self.log("Found Post button by class.")
                    except:
                        pass

                if not post_btn:
                     raise Exception("Post button not found with any selector")

                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post_btn)
                time.sleep(2)

                click_success = False
                for i in range(3):
                    try:
                        self.log(f"Click attempt {i+1}...")

                        if (i + 1) % 2 != 0:

                            self.driver.execute_script("arguments[0].click();", post_btn)
                        else:

                            post_btn.click()

                        self.log("Waiting for response...")
                        time.sleep(5)

                        if "upload" not in self.driver.current_url:
                            click_success = True
                            break

                        try:
                            if not post_btn.is_displayed():
                                self.log("Button disappeared.")
                                click_success = True
                                break
                            if post_btn.get_attribute("disabled") or post_btn.get_attribute("data-loading") == "true":
                                self.log("Button entered loading state.")
                                click_success = True
                                break
                        except:

                            self.log("Button element stale (page updated).")
                            click_success = True
                            break

                        self.log("Click seemingly ineffective, retrying...")
                    except Exception as e:
                        self.log(f"Click error: {e}")
                        time.sleep(2)

                if click_success:
                    self.log("✅ TikTok: 'Post' button click registered.")
                else:
                    self.log("⚠ Warning: Click might not have registered.")

                self.log("⏳ Waiting for upload confirmation...")
                upload_success = False
                wait_start = time.time()

                while time.time() - wait_start < 60:
                    try:

                        if "upload" not in self.driver.current_url:
                            self.log("✅ Redirected from upload page. Upload likely successful.")
                            upload_success = True
                            break

                        src = self.driver.page_source
                        if "Video uploaded" in src or "Upload another video" in src or "Manage your posts" in src:
                            self.log("✅ Success message detected.")
                            upload_success = True
                            break

                        time.sleep(2)
                    except:
                        time.sleep(1)

                if not upload_success:
                    self.log("⚠ Warning: No upload confirmation detected, but time expired.")
                    self.log("Leaving browser open for a few more seconds...")
                    time.sleep(10)
                else:

                    time.sleep(5)

                return "Success"
            except Exception as e:
                self.log(f"⚠ Auto-Post Click Failed: {e}")
                self.log("⚠ Please click POST manually.")
                return "Manual Completion Required"

        except Exception as e:
            return f"Error: {e}"

    def upload_instagram(self, file_path, caption):
        if "Instagram" not in self.windows: return "Window not found"
        try:
            self.driver.switch_to.window(self.windows["Instagram"])
        except:
            return "Browser Window Closed"

        self.log("Instagram: Starting upload process...")
        
        try:
            create_btn = None
            try:
                try:
                    create_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='Create']"))
                    )
                except:
                    try:
                        create_btn = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, "//svg[@aria-label='New post']"))
                        )
                        create_btn = create_btn.find_element(By.XPATH, "./../../..")
                    except:
                        pass

                if create_btn:
                    try: create_btn.click()
                    except: self.driver.execute_script("arguments[0].click();", create_btn)
                    self.log("IG: Clicked 'Create'.")
                    time.sleep(2)
                else:
                    self.log("IG: 'Create' button not found (Auto-detection failed).")
                    
            except Exception as e:
                self.log(f"IG: Error clicking Create: {e}")

            try:
                post_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Post']"))
                )
                try: post_btn.click()
                except: self.driver.execute_script("arguments[0].click();", post_btn)
                self.log("IG: Clicked 'Post'.")
                time.sleep(2)
            except:
                self.log("IG: 'Post' menu item not found (Maybe direct upload?). Proceeding...")

            try:
                file_path = os.path.abspath(file_path)
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )

                self.driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = '1';
                    arguments[0].style.width = '1px';
                    arguments[0].style.height = '1px';
                    arguments[0].style.overflow = 'visible';
                    arguments[0].style.zIndex = '999999';
                """, file_input)
                time.sleep(1)
                
                file_input.send_keys(file_path)
                self.log("IG: File selected.")
                time.sleep(5)
            except Exception as e:
                self.log(f"IG: File input error: {e}")
                self.log("IG: Please upload manually.")
                return "Manual Completion Required"

            try:
                self.log("IG: Attempting to set aspect ratio to 9:16...")
                crop_btn = None
                crop_xpaths = [
                    "//svg[@aria-label='Select crop']",
                    "//svg[@aria-label='Select crop']/parent::div",
                    "//div[@class='html-div xdj266r x14z9mp xat24cr x1lziwak x9f619 xjbqb8w x78zum5 x15mokao x1ga7v0g x16uus16 xbiv7yw x1y1aw1k xf159sx xwib8y2 xmzvs34 x1n2onr6 x1plvlek xryxfnj x1c4vz4f x2lah0s x1q0g3np xqjyukv x6s0dn4 x1oa3qoh xl56j7k']",                           
                    "//svg[@aria-label='Crop']",
                    "//svg[@aria-label='เลือกการครอบตัด']", 
                    "//svg[@aria-label='ครอบตัด']",
                    "//div[@role='button']//svg[@aria-label='Select crop']",
                    "//button//svg[@aria-label='Select crop']"
                ]
                
                for xpath in crop_xpaths:
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        crop_btn = element
                        self.log(f"IG: Found crop button with xpath: {xpath}")
                        break
                    except:
                        continue

                if crop_btn:
                    try: 
                        crop_btn.click()
                    except:
                        try:
                             self.driver.execute_script("arguments[0].click();", crop_btn)
                        except:
                             self.driver.execute_script("arguments[0].parentElement.click();", crop_btn)
                else:
                    raise Exception("Crop button not found")
                
                time.sleep(1)
                ratio_btn = None
                ratio_xpaths = [
                    "//svg[@aria-label='Crop portrait icon']",
                    "//svg[@aria-label='Crop portrait icon']/ancestor::div[@role='button']",
                    "//span[contains(text(), '9:16')]/ancestor::div[@role='button']",
                    "//span[contains(text(), '9:16')]",
                    "//div[@aria-label='9:16']"
                ]

                for xpath in ratio_xpaths:
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                             EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        ratio_btn = element
                        self.log(f"IG: Found 9:16 button with xpath: {xpath}")
                        break
                    except:
                        continue
                
                if ratio_btn:
                    try: ratio_btn.click()
                    except: self.driver.execute_script("arguments[0].click();", ratio_btn)
                    self.log("IG: Selected 9:16 aspect ratio.")
                else:
                    self.log("IG: 9:16 option not found.")

            except Exception as e:
                self.log(f"IG: Note - Could not set 9:16 ratio (Error: {e}). Proceeding...")

                                                   
            def safe_click_ig(xpath, name="Element", timeout=10):
                try:
                                                   
                    try:
                        popups = self.driver.find_elements(By.XPATH, "//button[text()='Not Now'] | //button[text()='Cancel'] | //div[@role='dialog']//button[contains(text(), 'Not Now')]")
                        for p in popups:
                            if p.is_displayed():
                                p.click()
                                time.sleep(1)
                    except: pass

                    btn = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                    time.sleep(1)
                    
                    try:
                        btn.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", btn)
                    
                    self.log(f"IG: Clicked {name}.")
                    return True
                except Exception as e:
                    self.log(f"IG: Failed to click {name} ({e})")
                    return False

                              
            if not safe_click_ig("//div[text()='Next' or text()='ถัดไป']", "Next (Crop)"):
                 self.log("IG: Retrying Crop Next with generic selector...")
                 safe_click_ig("//button[contains(text(), 'Next')]", "Next (Button)")

            time.sleep(2)

                                      
            try:
                self.log("IG: Checking for Cover selection...")
                time.sleep(2)

                                         
                try:
                    cover_tabs = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'Cover')] | //div[contains(text(), 'Cover')] | //span[contains(text(), 'หน้าปก')] | //div[contains(text(), 'หน้าปก')]")
                    for tab in cover_tabs:
                        if tab.is_displayed():
                            try:
                                tab.click()
                                self.log("IG: Switched to Cover tab.")
                                time.sleep(2)
                                break
                            except: pass
                except: pass

                                         
                try:
                    thumbs = self.driver.find_elements(By.XPATH, "//div[@role='button']//img")
                    valid_thumbs = [t for t in thumbs if t.size['width'] > 50]
                    
                    if valid_thumbs:
                        if len(valid_thumbs) >= 3:
                            valid_thumbs[1].click()
                            self.log("IG: Selected middle cover thumbnail.")
                        elif len(valid_thumbs) > 0:
                            valid_thumbs[0].click()
                            self.log("IG: Selected available cover thumbnail.")
                except Exception as e:
                    self.log(f"IG: Thumbnail selection failed: {e}")

                                      
                try:
                    slider = self.driver.find_element(By.XPATH, "//input[@type='range']")
                    if slider.is_displayed():
                        self.driver.execute_script("arguments[0].value = 50; arguments[0].dispatchEvent(new Event('change'));", slider)
                        self.log("IG: Adjusted cover slider.")
                except: pass
                
                time.sleep(1)

                                           
                if not safe_click_ig("//div[text()='Next' or text()='ถัดไป']", "Next (Filter/Cover)"):
                    self.log("IG: Retrying Filter Next...")
                    safe_click_ig("//div[@role='button'][contains(., 'Next')]", "Next (Role Button)")

                time.sleep(2)
            except Exception as e:
                self.log(f"IG: Error during Filter/Cover step: {e}")
                
                        
            try:
                caption_area = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Write a caption...']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", caption_area)
                time.sleep(1)

                try:
                    caption_area.click()
                except:
                    self.driver.execute_script("arguments[0].click();", caption_area)
                
                time.sleep(1)
                import pyperclip
                pyperclip.copy(caption)
                caption_area.send_keys(Keys.CONTROL, 'v')
                
                self.log("IG: Caption added.")
                time.sleep(2)
            except:
                self.log("IG: Caption area not found.")

                      
            if not safe_click_ig("//div[text()='Share' or text()='โพสต์' or text()='Share']", "Share"):
                self.log("IG: Retrying Share click...")
                if not safe_click_ig("//div[@role='button'][contains(., 'Share')]", "Share (Role Button)"):
                     self.log("IG: 'Share' button not found or not clickable.")
                     return "Manual Completion Required"

                             
            self.log("IG: Waiting for upload confirmation...")
            start_wait = time.time()
            success = False
            while time.time() - start_wait < 60:
                try:
                    src = self.driver.page_source
                    if "Post shared" in src or "Your reel has been shared" in src:
                        self.log("✅ IG: Post Shared Successfully!")
                        success = True
                        break
                except Exception as e:
                     if "invalid session id" in str(e) or "no such execution context" in str(e) or "disconnected" in str(e):
                         self.log("⚠ IG: Browser closed/disconnected during verification.")
                         break
                time.sleep(2)

            if success:
                try:
                     close_btn = self.driver.find_element(By.XPATH, "//svg[@aria-label='Close']")
                     close_btn_container = close_btn.find_element(By.XPATH, "./../../..")
                     try: close_btn_container.click()
                     except: self.driver.execute_script("arguments[0].click();", close_btn_container)
                except: pass
                return "Success"
            else:
                self.log("⚠ IG: Confirmation not detected.")
                return "Manual Check"

        except Exception as e:
            self.log(f"IG Error: {e}")
            return "Error"

    def upload_shorts(self, file_path, caption):
        if "Shorts" not in self.windows: return "Window not found"
        try:
            self.driver.switch_to.window(self.windows["Shorts"])
        except:
            return "Browser Window Closed"

        self.log("Shorts: Please click 'Create' -> 'Upload videos'.")
        return "Manual Completion Required"

    def upload_facebook(self, file_path, caption):
        if "Facebook" not in self.windows: return "Window not found"
        try:
            self.driver.switch_to.window(self.windows["Facebook"])
        except:
            return "Browser Window Closed"

        self.log("Facebook: Starting upload process...")
        
        try:
            if "reels/create" not in self.driver.current_url:
                self.driver.get("https://www.facebook.com/reels/create")
                time.sleep(3)

            try:
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                file_input.send_keys(file_path)
                self.log("Facebook: File uploaded.")
                time.sleep(5)
            except Exception as e:
                self.log(f"Facebook: File upload failed. {e}")
                return "Manual Completion Required"

            try:
                self.log("Facebook: Looking for Next/Upload button (Step 1)...")
                step1_clicked = False
                for _ in range(10):
                    try:
                         btn = None
                         potential_btns = self.driver.find_elements(By.XPATH, "//span[text()='Next' or text()='Upload']")
                         
                         for b in potential_btns:
                             if b.is_displayed():
                                 try:
                                     b.click()
                                     step1_clicked = True
                                     break
                                 except:
                                     try:
                                         self.driver.execute_script("arguments[0].click();", b)
                                         step1_clicked = True
                                         break
                                     except: pass
                         
                         if step1_clicked: break
                    except: pass
                    time.sleep(2)
                
                if step1_clicked:
                    self.log("Facebook: Clicked First Next/Upload.")
                else:
                    self.log("Facebook: Could not find first Next/Upload button.")
                
                time.sleep(3)
                self.log("Facebook: Looking for Next button (Step 2)...")
                step2_clicked = False
                for _ in range(5):
                    try:
                        potential_btns = self.driver.find_elements(By.XPATH, "//span[text()='Next']")
                        for b in potential_btns:
                             if b.is_displayed():
                                 b.click()
                                 step2_clicked = True
                                 break
                        if step2_clicked: break
                    except: pass
                    time.sleep(2)
                
                if step2_clicked:
                     self.log("Facebook: Clicked Second Next.")
                
                time.sleep(3)
                self.log("Facebook: Looking for Caption box...")
                try:
                    caption_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                    )
                
                    try: caption_box.click()
                    except: self.driver.execute_script("arguments[0].click();", caption_box)
        
                    time.sleep(1)
                
                    import pyperclip
                    pyperclip.copy(caption)
                    caption_box.send_keys(Keys.CONTROL, "v")
                    self.log("Facebook: Caption filled.")
                    
                except Exception as e:
                    self.log(f"Facebook: Caption failed (might be different layout). {e}")

                time.sleep(2)
                self.log("Facebook: Attempting to click Post/Publish...")
                
                post_xpaths = [
                    "//span[text()='Post']",
                    "//span[text()='Publish']",
                    "//div[text()='Post']",
                    "//div[text()='Publish']",
                    "//div[@role='button']//span[contains(text(), 'Post')]",
                    "//div[@role='button']//div[contains(text(), 'Post')]",
                    "//div[@aria-label='Post']"
                ]

                for i in range(30):
                    found_btn = None
                    for xpath in post_xpaths:
                        try:
                            btns = self.driver.find_elements(By.XPATH, xpath)
                            for btn in btns:
                                if btn.is_displayed():
                                    found_btn = btn
                                    break
                        except: pass
                        if found_btn: break
                    
                    if found_btn:
                        try:
                            aria_disabled = found_btn.get_attribute("aria-disabled")
                            is_disabled = found_btn.get_attribute("disabled")
                            parent_disabled = False
                            try:
                                parent = found_btn.find_element(By.XPATH, "./..")
                                if parent.get_attribute("aria-disabled") == "true":
                                    parent_disabled = True
                            except: pass

                            if aria_disabled == "true" or is_disabled or parent_disabled:
                                if i % 5 == 0:
                                    self.log(f"Facebook: Post button found but disabled. Waiting... ({i}/30)")
                                time.sleep(1)
                                continue
                            
                                           
                            try: found_btn.click()
                            except: self.driver.execute_script("arguments[0].click();", found_btn)
                            
                            self.log("Facebook: Clicked Post/Publish.")
                            time.sleep(5)
                            return "Success"
                        except Exception as e:
                             self.log(f"Facebook: Error interacting with Post button: {e}")
                    
                    if i % 5 == 0 and not found_btn:
                         self.log(f"Facebook: Searching for Post button... ({i}/30)")
                    
                    time.sleep(1)
                
                self.log("Facebook: Post button not found or remained disabled. Please finish manually.")
                return "Manual Completion Required"

            except Exception as e:
                 self.log(f"Facebook Flow Error: {e}")
                 return "Manual Completion Required"

        except Exception as e:
            self.log(f"Facebook Error: {e}")
            return "Error"

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

                                                                                
                        
                                                                                
                                                                               
                                                                                           
                                                                                
class AssetDownloader(ctk.CTkFrame):
    def __init__(self, parent, settings_ref, app_instance):
        super().__init__(parent)
        self.settings = settings_ref
        self.app = app_instance
        self.queue = []
        self.current_asset = None
        self.page = 1
        self.music_page = 1
        self.total_results = 0
        self.video_results = []
        self.video_vars = []
        self.music_results = []
        self.music_vars = []
        self.current_preview_file = None
        
        try:
            pygame.mixer.init()
        except:
            pass

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

                                  
        try:
            with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                q_data = json.load(f)
                self.dl_themes = list(q_data.keys())
        except:
            self.dl_themes = ["love", "sad", "motivation", "development", "life"]
            
            
        self.var_dl_theme = ctk.StringVar(value="Love")

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tab_view.add("Videos")
        self.tab_view.add("Music")
        self.tab_view.add("Settings")
        self.tab_view.set("Videos")
        self.frame_pexels = ctk.CTkFrame(self.tab_view.tab("Videos"), fg_color="transparent")
        self.frame_pexels.pack(fill="both", expand=True)

        p_search_frame = ctk.CTkFrame(self.frame_pexels, fg_color="transparent")
        p_search_frame.pack(fill="x", padx=10, pady=10)

        self.entry_pexels = ctk.CTkEntry(p_search_frame, placeholder_text="Search Pexels...", width=140, fg_color=self.app.color_input_bg, font=("Roboto", 12))
        self.entry_pexels.pack(side="left", padx=5)
        self.entry_pexels.insert(0, "Love")
        self.chk_vertical = ctk.CTkCheckBox(p_search_frame, text="9:16", width=60, onvalue=True, offvalue=False, font=("Roboto", 11))
        self.chk_vertical.select()
        self.chk_vertical.pack(side="left", padx=5)

        ctk.CTkButton(p_search_frame, text="SEARCH", command=lambda: self.search("pexels"), width=80, fg_color=self.app.color_accent, hover_color=self.app.color_accent_hover, font=("Roboto", 12, "bold")).pack(side="left", padx=5)

        self.btn_prev = ctk.CTkButton(p_search_frame, text="<", width=30, command=lambda: self.change_page(-1), fg_color="#444", font=("Roboto", 12, "bold"))
        self.btn_prev.pack(side="left", padx=(10, 5))
        self.lbl_page = ctk.CTkLabel(p_search_frame, text=f"Page {self.page}", font=("Roboto", 12, "bold"))
        self.lbl_page.pack(side="left", padx=5)
        self.btn_next = ctk.CTkButton(p_search_frame, text=">", width=30, command=lambda: self.change_page(1), fg_color="#444", font=("Roboto", 12, "bold"))
        self.btn_next.pack(side="left", padx=5)

        ctk.CTkLabel(p_search_frame, text="Save:", font=("Roboto", 12, "bold")).pack(side="left", padx=(10, 2))
        self.combo_theme_video = ctk.CTkComboBox(p_search_frame, values=self.dl_themes, width=100, state="readonly", variable=self.var_dl_theme, fg_color=self.app.color_input_bg, button_color=self.app.color_accent, font=("Roboto", 12))
        self.combo_theme_video.pack(side="left", padx=2)

        ctk.CTkButton(p_search_frame, text="Download", command=self.download_selected_videos, fg_color="green", width=80, font=("Roboto", 12, "bold")).pack(side="right", padx=2)
        ctk.CTkButton(p_search_frame, text="Clear", command=self.clear_selection, fg_color="#555", width=60, font=("Roboto", 11)).pack(side="right", padx=2)
        ctk.CTkButton(p_search_frame, text="Select All", command=self.select_all_videos, fg_color="#444", width=70, font=("Roboto", 11)).pack(side="right", padx=2)

        self.scroll_videos = ctk.CTkFrame(self.frame_pexels, fg_color="#222")
        self.scroll_videos.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.scroll_videos.grid_columnconfigure((0,1,2,3,4), weight=1)            

        self.frame_pixabay = ctk.CTkFrame(self.tab_view.tab("Music"), fg_color="transparent")
        self.frame_pixabay.pack(fill="both", expand=True)

        m_search_frame = ctk.CTkFrame(self.frame_pixabay, fg_color="transparent")
        m_search_frame.pack(fill="x", padx=10, pady=10)

        self.entry_pixabay = ctk.CTkEntry(m_search_frame, placeholder_text="Search Music...", width=140, fg_color=self.app.color_input_bg, font=("Roboto", 12))
        self.entry_pixabay.pack(side="left", padx=5)
        self.entry_pixabay.bind("<Return>", lambda e: self.search("pixabay"))

        ctk.CTkButton(m_search_frame, text="SEARCH", command=lambda: self.search("pixabay"), width=80, fg_color=self.app.color_accent, hover_color=self.app.color_accent_hover, font=("Roboto", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(m_search_frame, text="⏹ Stop", command=self.stop_music_preview, fg_color="#C62828", width=50, font=("Roboto", 11)).pack(side="left", padx=5)
        ctk.CTkButton(m_search_frame, text="Import", command=self.import_music, fg_color="#555", width=50, font=("Roboto", 11)).pack(side="left", padx=5)

        self.btn_m_prev = ctk.CTkButton(m_search_frame, text="<", width=30, command=lambda: self.change_music_page(-1), fg_color="#444", font=("Roboto", 12, "bold"))
        self.btn_m_prev.pack(side="left", padx=(10, 5))
        self.lbl_m_page = ctk.CTkLabel(m_search_frame, text=f"Page {self.music_page}", font=("Roboto", 12, "bold"))
        self.lbl_m_page.pack(side="left", padx=5)
        self.btn_m_next = ctk.CTkButton(m_search_frame, text=">", width=30, command=lambda: self.change_music_page(1), fg_color="#444", font=("Roboto", 12, "bold"))
        self.btn_m_next.pack(side="left", padx=5)
        
        ctk.CTkLabel(m_search_frame, text="Save:", font=("Roboto", 12, "bold")).pack(side="left", padx=(10, 2))
        self.combo_theme_music = ctk.CTkComboBox(m_search_frame, values=self.dl_themes, width=100, state="readonly", variable=self.var_dl_theme, fg_color=self.app.color_input_bg, button_color=self.app.color_accent, font=("Roboto", 12))
        self.combo_theme_music.pack(side="left", padx=2)
        
        ctk.CTkButton(m_search_frame, text="Download", command=self.download_selected_music, fg_color="green", width=80, font=("Roboto", 12, "bold")).pack(side="right", padx=2)
        ctk.CTkButton(m_search_frame, text="Clear", command=self.clear_music_selection, fg_color="#555", width=60, font=("Roboto", 11)).pack(side="right", padx=2)
        ctk.CTkButton(m_search_frame, text="Select All", command=self.select_all_music, fg_color="#444", width=70, font=("Roboto", 11)).pack(side="right", padx=2)

        self.scroll_music = ctk.CTkScrollableFrame(self.frame_pixabay, fg_color="#222", scrollbar_button_color="#222", scrollbar_button_hover_color="#222")                          
        self.scroll_music._scrollbar.configure(width=0)
        self.scroll_music.pack(fill="both", expand=True, padx=10, pady=0)
        self.lbl_music_status = ctk.CTkLabel(self.scroll_music, text="Enter keyword to search music.", text_color="gray")
        self.lbl_music_status.pack(pady=20)
        self.frame_settings = ctk.CTkFrame(self.tab_view.tab("Settings"), fg_color="transparent")
        self.frame_settings.pack(fill="both", expand=True, padx=10, pady=10)

                                              
        self.frame_api = ctk.CTkFrame(self.frame_settings, fg_color="#333", corner_radius=10)
        self.frame_api.pack(fill="x", pady=(0, 10), ipady=5)
        
        ctk.CTkLabel(self.frame_api, text="API Configuration", font=("Roboto", 14, "bold")).pack(pady=5)
        
        self.entry_key_pexels = ctk.CTkEntry(self.frame_api, placeholder_text="Pexels API Key", width=350, fg_color=self.app.color_input_bg)
        self.entry_key_pexels.pack(pady=5)
        if "pexels_key" in self.settings:
            self.entry_key_pexels.insert(0, self.settings["pexels_key"])

        self.entry_key_pixabay = ctk.CTkEntry(self.frame_api, placeholder_text="Pixabay API Key (Optional)", width=350, fg_color=self.app.color_input_bg)
        self.entry_key_pixabay.pack(pady=5)
        if "pixabay_key" in self.settings:
            self.entry_key_pixabay.insert(0, self.settings["pixabay_key"])

        ctk.CTkButton(self.frame_api, text="Save API Keys", command=self.save_keys, width=150, fg_color=self.app.color_accent, hover_color=self.app.color_accent_hover).pack(pady=10)

                                                      
        self.frame_status = ctk.CTkFrame(self.frame_settings, fg_color="transparent")
        self.frame_status.pack(fill="both", expand=True, pady=(0, 10))
        
        status_header = ctk.CTkFrame(self.frame_status, fg_color="transparent")
        status_header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(status_header, text="Downloaded Assets Status", font=("Roboto", 14, "bold")).pack(side="left")
        
        self.btn_refresh_stats = ctk.CTkButton(status_header, text="Refresh", command=self.update_asset_stats, width=80, height=25, fg_color="#555", hover_color="#666")
        self.btn_refresh_stats.pack(side="right")
        
                                       
        self.frame_asset_stats = ctk.CTkScrollableFrame(self.frame_status, fg_color="#2b2b2b")
        self.frame_asset_stats.pack(fill="both", expand=True)

                                      
        self.frame_utils_container = ctk.CTkFrame(self.frame_settings, fg_color="#333", corner_radius=10)
        self.frame_utils_container.pack(fill="x", pady=0, ipady=5)
        
        ctk.CTkLabel(self.frame_utils_container, text="Utilities", font=("Roboto", 14, "bold")).pack(pady=5)
        
        utils_btns = ctk.CTkFrame(self.frame_utils_container, fg_color="transparent")
        utils_btns.pack(pady=5)

        self.btn_open_folder = ctk.CTkButton(utils_btns, text="Open Output Folder", command=lambda: os.startfile(DIRS["output"]), fg_color="transparent", border_width=1, width=160)
        self.btn_open_folder.pack(side="left", padx=10)
        self.app.btn_open_folder = self.btn_open_folder

        self.btn_check_corrupted = ctk.CTkButton(utils_btns, text="Check Corrupted Videos", command=self.app.check_corrupted_videos, fg_color="#AA0000", hover_color="#880000", width=160)
        self.btn_check_corrupted.pack(side="left", padx=10)
        self.app.btn_check_corrupted = self.btn_check_corrupted

        self.lbl_info = ctk.CTkLabel(self, text="", font=("Helvetica", 16), fg_color="#333", corner_radius=10)
        self.progress_bar = ctk.CTkProgressBar(self, width=300, height=15, corner_radius=5)
        self.progress_bar.set(0)
        self.after(500, lambda: self.search("pexels"))
        self.entry_pixabay.insert(0, "Love")
        self.after(1000, lambda: self.search("pixabay"))
        self.after(1500, self.update_asset_stats)

    def update_asset_stats(self):
        for widget in self.frame_asset_stats.winfo_children():
            widget.destroy()
            
                      
        video_counts = {}
        bg_root = "assets/backgrounds"
        if os.path.exists(bg_root):
            for theme in os.listdir(bg_root):
                path = os.path.join(bg_root, theme)
                if os.path.isdir(path):
                    count = len([f for f in os.listdir(path) if f.endswith(('.mp4', '.mov'))])
                    video_counts[theme] = count
                    
                     
        music_counts = {}
        music_root = "assets/music"
        if os.path.exists(music_root):
            for theme in os.listdir(music_root):
                path = os.path.join(music_root, theme)
                if os.path.isdir(path):
                    count = len([f for f in os.listdir(path) if f.endswith(('.mp3', '.wav'))])
                    music_counts[theme] = count
        
                 
        themes = sorted(list(set(list(video_counts.keys()) + list(music_counts.keys()))))
        
        if not themes:
             ctk.CTkLabel(self.frame_asset_stats, text="No assets downloaded yet.", text_color="gray").pack(pady=10)
             return

                                                        
        self.frame_asset_stats.grid_columnconfigure(0, weight=1)
        self.frame_asset_stats.grid_columnconfigure(1, weight=1)
        self.frame_asset_stats.grid_columnconfigure(2, weight=1)
        
                 
        ctk.CTkLabel(self.frame_asset_stats, text="THEME", font=("Roboto", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 2))
        ctk.CTkLabel(self.frame_asset_stats, text="VIDEOS", font=("Roboto", 12, "bold"), anchor="center").grid(row=0, column=1, sticky="ew", pady=(5, 2))
        ctk.CTkLabel(self.frame_asset_stats, text="MUSIC", font=("Roboto", 12, "bold"), anchor="center").grid(row=0, column=2, sticky="ew", pady=(5, 2))
        
                 
        ctk.CTkFrame(self.frame_asset_stats, fg_color="gray", height=2).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        for i, theme in enumerate(themes):
             v_count = video_counts.get(theme, 0)
             m_count = music_counts.get(theme, 0)
             
             row = i + 2
             
                         
             ctk.CTkLabel(self.frame_asset_stats, text=theme.capitalize(), font=("Roboto", 12), anchor="w").grid(row=row, column=0, sticky="ew", padx=10, pady=2)
             
                          
             lbl_v = ctk.CTkLabel(self.frame_asset_stats, text=str(v_count), font=("Roboto", 12, "bold"), text_color="#4CAF50" if v_count > 0 else "#F44336")
             lbl_v.grid(row=row, column=1, sticky="ew", pady=2)
             
                          
             lbl_m = ctk.CTkLabel(self.frame_asset_stats, text=str(m_count), font=("Roboto", 12, "bold"), text_color="#2196F3" if m_count > 0 else "#F44336")
             lbl_m.grid(row=row, column=2, sticky="ew", pady=2)

    def search(self, source):
        if source == "pexels":
            self.page = 1
            self.lbl_page.configure(text=f"Page {self.page}")
        elif source == "pixabay":
            self.music_page = 1
            self.lbl_m_page.configure(text=f"Page {self.music_page}")
        
        self.lbl_info.configure(text="Searching...", text_color="white")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        threading.Thread(target=self.run_search, args=(source,)).start()

    def change_page(self, delta):
        new_page = self.page + delta
        if new_page < 1: return
        
        self.page = new_page
        self.lbl_page.configure(text=f"Page {self.page}")
        self.lbl_info.configure(text=f"Loading Page {self.page}...", text_color="white")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        threading.Thread(target=self.run_search, args=("pexels",)).start()

    def change_music_page(self, delta):
        new_page = self.music_page + delta
        if new_page < 1: return
        
        self.music_page = new_page
        self.lbl_m_page.configure(text=f"Page {self.music_page}")
        self.lbl_info.configure(text=f"Loading Page {self.music_page}...", text_color="white")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        
        threading.Thread(target=self.run_search, args=("pixabay",)).start()

    def run_search(self, source):
        try:
            if source == "pexels":
                self.search_pexels()
            elif source == "pixabay":
                self.search_pixabay()
        except Exception as e:
            self.lbl_info.configure(text=f"Error: {e}")
            self.after(3000, self.lbl_info.place_forget)

    def search_pexels(self):
        query = self.entry_pexels.get()
        api_key = self.settings.get("pexels_key")
        if not api_key:
            self.lbl_info.configure(text="Error: Pexels API Key required.")
            return

        headers = {"Authorization": api_key}
        orientation = "portrait" if self.chk_vertical.get() else "landscape"
        url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=10&page={self.page}"

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.total_results = data.get("total_results", 0)
                videos = data.get("videos", [])
                
                self.video_results = []
                for v in videos:
                    video_files = v.get("video_files", [])
                    best = next((f for f in video_files if f["width"] >= 720 and f["width"] <= 1920), video_files[0] if video_files else None)
                    if best:
                        self.video_results.append({
                            "type": "video",
                            "id": v["id"],
                            "title": f"Video {v['id']}",
                            "user": v["user"]["name"],
                            "duration": v["duration"],
                            "thumb": v["image"],
                            "download_url": best["link"],
                            "preview_url": best["link"],
                            "page_url": v["url"]
                        })
                
                self.after(0, self.update_video_grid)
            else:
                self.lbl_info.configure(text=f"API Error: {resp.status_code}")
                self.after(2000, self.lbl_info.place_forget)
        except Exception as e:
            self.lbl_info.configure(text=f"Network Error: {e}")
            self.after(2000, self.lbl_info.place_forget)

    def update_video_grid(self):
        for widget in self.scroll_videos.winfo_children():
            widget.destroy()
        self.video_vars = []

        if not self.video_results:
            self.lbl_info.configure(text="No videos found.")
            self.after(2000, self.lbl_info.place_forget)
        else:
            self.lbl_info.place_forget()

            for i, vid in enumerate(self.video_results):
                row = i // 5
                col = i % 5
                card = ctk.CTkFrame(self.scroll_videos, fg_color="#333", corner_radius=8)
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                lbl_thumb = ctk.CTkLabel(card, text="Loading...", width=135, height=240, fg_color="#000", corner_radius=5)
                lbl_thumb.pack(padx=5, pady=5, expand=True)
                info_text = f"{vid['duration']}s\n{vid['user'][:10]}"
                ctk.CTkLabel(card, text=info_text, font=("Arial", 10), text_color="gray").pack()
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(card, text="Select", variable=var, font=("Arial", 11), width=60, height=20)
                chk.pack(pady=(0, 3))
                self.video_vars.append((vid, var))
                threading.Thread(target=self.load_thumbnail_to_label, args=(vid["thumb"], lbl_thumb)).start()
        try:
            if self.page <= 1:
                self.btn_prev.configure(state="disabled", fg_color="gray")
            else:
                self.btn_prev.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"))

            total_pages = math.ceil(self.total_results / 10)
            if self.page >= total_pages and total_pages > 0:
                 self.btn_next.configure(state="disabled", fg_color="gray")
            else:
                 self.btn_next.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"))
        except Exception as e:
            pass

    def load_thumbnail_to_label(self, url, label_widget):
        try:
            resp = requests.get(url, timeout=5)
            img_data = io.BytesIO(resp.content)
            pil_img = Image.open(img_data)
            w, h = pil_img.size
            target_w = 135
            ratio = target_w / w
            target_h = int(h * ratio)
            pil_img = pil_img.resize((target_w, target_h))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(target_w, target_h))
            
            self.after(0, lambda: label_widget.configure(image=ctk_img, text=""))
        except:
            self.after(0, lambda: label_widget.configure(text="Error"))

    def select_all_videos(self):
        for _, var in self.video_vars:
            var.set(True)

    def clear_selection(self):
        for _, var in self.video_vars:
            var.set(False)

    def download_selected_videos(self):
        selected = [v for v, var in self.video_vars if var.get()]
        if not selected:
            return
        
        self.lbl_info.configure(text=f"Downloading {len(selected)} videos...", text_color="#4CAF50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        threading.Thread(target=self.run_bulk_download, args=(selected,)).start()

    def run_bulk_download(self, assets):
        total = len(assets)
        count = 0
        duplicates = 0
        self.after(0, lambda: self.progress_bar.place(relx=0.5, rely=0.6, anchor="center"))
        self.after(0, lambda: self.progress_bar.set(0))
        existing_music_ids = set()
        if assets and assets[0].get("type") == "music":
            try:
                if os.path.exists("assets/music"):
                    for f in os.listdir("assets/music"):
                        clean_id = f.split("_")[0].split(".")[0]
                        existing_music_ids.add(clean_id)
            except Exception as e:
                print(f"Error checking existing music: {e}")

        for i, asset in enumerate(assets):
            try:
                if asset.get("type") == "music":
                    asset_id = str(asset.get("id"))
                    if asset_id in existing_music_ids:
                        duplicates += 1
                        progress = (i + 1) / total
                        self.after(0, lambda p=progress: self.progress_bar.set(p))
                        continue
                
                self.download_asset(asset)
                count += 1
            except: pass
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda c=count, d=duplicates: self.lbl_info.configure(text=f"Downloading... {c}/{total} (Dupes: {d})"))
        
        msg = f"Downloaded {count} files!"
        if duplicates > 0:
            msg += f" (Skipped {duplicates} duplicates)"
        
        self.after(0, lambda: self.lbl_info.configure(text=msg))
        self.after(3000, self.lbl_info.place_forget)
        self.after(3000, self.progress_bar.place_forget)

    def search_pixabay(self):
        query = self.entry_pixabay.get()
        if not query:
             self.lbl_info.configure(text="Enter keyword.")
             self.after(2000, self.lbl_info.place_forget)
             return

        self.lbl_info.configure(text="Searching Pixabay Music...", text_color="white")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        threading.Thread(target=self.run_pixabay_scrape, args=(query,)).start()

    def parse_pixabay_json(self, data):
        try:
            results = data.get("page", {}).get("results", [])
            
            for item in results:
                m_id = item.get("id")
                title = item.get("name") or item.get("alt") or item.get("description") or f"Track {m_id}"
                duration_sec = item.get("duration", 0)
                mins = duration_sec // 60
                secs = duration_sec % 60
                dur_str = f"{mins}:{secs:02d}"
                sources = item.get("sources", {})
                stream_url = sources.get("src")
                
                if stream_url:
                    self.music_results.append({
                        "id": m_id,
                        "type": "music",
                        "title": title,
                        "duration": dur_str,
                        "preview_url": stream_url,
                        "download_url": stream_url,
                        "author": item.get("user", {}).get("username", "Pixabay")
                    })
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    def parse_pixabay_regex(self, html_content):
        try:
            mp3_pattern = r'https://cdn\.pixabay\.com/audio/[^\"]+\.mp3'
            found_urls = list(set(re.findall(mp3_pattern, html_content)))
            
            for i, m_url in enumerate(found_urls[:20]):
                try:
                    filename = m_url.split("/")[-1]
                    base_name = filename.replace(".mp3", "")
                    m_id = base_name
                    if m_id.startswith("audio_"):
                        m_id = m_id.replace("audio_", "")
                except:
                    m_id = f"regex_{i}"

                self.music_results.append({
                    "id": m_id,
                    "type": "music",
                    "title": f"Track {m_id}",
                    "duration": "?",
                    "preview_url": m_url,
                    "download_url": m_url,
                    "author": "Pixabay"
                })
        except Exception as e:
            print(f"Regex Parse Error: {e}")

    def scrape_pixabay_selenium(self, url):
        if not SELENIUM_AVAILABLE: return False
        options = Options()
        options.add_argument("--headless=new") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = None
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
            
            driver.get(url)
            title = driver.title
            if "Just a moment" in title or "Verify" in title:
                time.sleep(5)
            try:
                bootstrap_url = driver.execute_script("return window.__BOOTSTRAP_URL__")
                if bootstrap_url:
                    full_url = "https://pixabay.com" + bootstrap_url
                    driver.get(full_url)
                    content = ""
                    try:
                        content = driver.find_element(By.TAG_NAME, "pre").text
                    except:
                        content = driver.find_element(By.TAG_NAME, "body").text
                        
                    if content:
                        data = json.loads(content)
                        self.parse_pixabay_json(data)
                        if self.music_results: return True
            except Exception as e:
                pass

            if not self.music_results:
                html = driver.page_source
                self.parse_pixabay_regex(html)
                if self.music_results: return True
                
        except Exception as e:
            pass
        
        finally:
            if driver: driver.quit()
            
        return False

    def scrape_pixabay_cloudscraper(self, url):
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url)
        
        if resp.status_code != 200:
            self.after(0, lambda: self.lbl_info.configure(text=f"Error: {resp.status_code}"))
            self.after(2000, self.lbl_info.place_forget)
            return

        html_content = resp.text
        bootstrap_match = re.search(r'window\.__BOOTSTRAP_URL__\s*=\s*[\'"]([^\'"]+)[\'"]', html_content)
        
        if bootstrap_match:
            bootstrap_url = "https://pixabay.com" + bootstrap_match.group(1)
            b_resp = scraper.get(bootstrap_url)
            if b_resp.status_code == 200:
                data = b_resp.json()
                self.parse_pixabay_json(data)
                if self.music_results: return

        self.parse_pixabay_regex(html_content)

    def run_pixabay_scrape(self, query):
        url = f"https://pixabay.com/music/search/{query}/?pagi={self.music_page}"
        self.music_results = []
        success = False

        if SELENIUM_AVAILABLE:
            try:
                success = self.scrape_pixabay_selenium(url)
            except Exception as e:
                pass

        if not success:
            try:
                self.scrape_pixabay_cloudscraper(url)
            except Exception as e:
                self.after(0, lambda: self.lbl_info.configure(text="Scrape Error"))
                self.after(2000, self.lbl_info.place_forget)
        
        try:
            self.after(0, lambda: self.update_music_list(query))
        except RuntimeError:
            pass

    def update_music_list(self, query):
        for widget in self.scroll_music.winfo_children():
            widget.destroy()
        self.music_vars = []
        self.lbl_info.place_forget()
        
        if not self.music_results:
            ctk.CTkLabel(self.scroll_music, text=f"No music found for '{query}'.", text_color="orange").pack(pady=20)
            return

        item_height = 58
        
        for i, music in enumerate(self.music_results):
            row = ctk.CTkFrame(self.scroll_music, fg_color="#333", height=item_height)
            row.pack(fill="x", padx=5, pady=3)

            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=30)
            chk.pack(side="left", padx=(10, 5))
            self.music_vars.append((music, var))
            
            ctk.CTkLabel(row, text="🎵", font=("Arial", 16)).pack(side="left", padx=5)

            title_lbl = ctk.CTkLabel(row, text=music["title"][:40], font=("Arial", 12, "bold"), anchor="w", width=250)
            title_lbl.pack(side="left", padx=5)
            
            ctk.CTkLabel(row, text=music["duration"], font=("Arial", 11), text_color="gray").pack(side="left", padx=10)
            btn_play = ctk.CTkButton(row, text="▶ Play", width=60, height=24, command=lambda m=music: self.play_music_preview(m))
            btn_play.pack(side="right", padx=10)
    
    def select_all_music(self):
        for _, var in self.music_vars:
            var.set(True)

    def clear_music_selection(self):
        for _, var in self.music_vars:
            var.set(False)

    def download_selected_music(self):
        selected = [m for m, var in self.music_vars if var.get()]
        if not selected:
            return
        
        self.lbl_info.configure(text=f"Downloading {len(selected)} tracks...", text_color="#4CAF50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        
        threading.Thread(target=self.run_bulk_download, args=(selected,)).start()

    def play_music_preview(self, music):
        if self.current_preview_file:
            self.stop_music_preview()
            
        self.lbl_info.configure(text=f"Loading: {music['title']}...", text_color="#4CAF50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        
        threading.Thread(target=self.run_music_preview, args=(music["preview_url"],)).start()

    def run_music_preview(self, url):
        try:
            temp_path = os.path.join("assets", "temp_preview.mp3")
            resp = requests.get(url, timeout=10)
            with open(temp_path, "wb") as f:
                f.write(resp.content)
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            self.current_preview_file = temp_path
            
            self.after(0, lambda: self.lbl_info.configure(text="Playing..."))
            self.after(1000, self.lbl_info.place_forget)
        except Exception as e:
            pass
            self.after(0, lambda: self.lbl_info.configure(text="Preview Failed"))
            self.after(2000, self.lbl_info.place_forget)

    def stop_music_preview(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except: pass
        self.current_preview_file = None

    def download_from_url(self):
        url = self.entry_dl_url.get()
        if not url: return
        self.download_asset({"type": "music", "id": f"url_{int(time.time())}", "download_url": url})
        self.lbl_info.configure(text="Download Started!")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
        self.after(2000, self.lbl_info.place_forget)

    def save_keys(self):
        self.settings["pexels_key"] = self.entry_key_pexels.get()
        self.settings["pixabay_key"] = self.entry_key_pixabay.get()
        try:
            with open("config/settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            pass

    def import_music(self):
        filename = filedialog.askopenfilename(title="Select Music", filetypes=[("Audio Files", "*.mp3;*.wav")])
        if filename:
            try:
                os.makedirs("assets/music", exist_ok=True)
                dest = os.path.join("assets/music", os.path.basename(filename))
                shutil.copy2(filename, dest)
                self.lbl_info.configure(text=f"Imported: {os.path.basename(filename)}")
                self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
                self.after(2000, self.lbl_info.place_forget)
            except Exception as e:
                self.lbl_info.configure(text=f"Error importing: {e}")
                self.after(2000, self.lbl_info.place_forget)

    def download_asset(self, asset):
        try:
                                      
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount("https://", adapter)
            http.mount("http://", adapter)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            resp = http.get(asset["download_url"], headers=headers, timeout=60)
            
                                                               
            theme = self.var_dl_theme.get()
            base_folder = "assets/backgrounds" if asset["type"] == "video" else "assets/music"
            folder = os.path.join(base_folder, theme)
            
            ext = ".mp4" if asset["type"] == "video" else ".mp3"
            os.makedirs(folder, exist_ok=True)
            
            filename = f"{asset['id']}_{int(time.time())}{ext}"
            path = os.path.join(folder, filename)
            
            with open(path, "wb") as f:
                f.write(resp.content)
                
            http.close()

        except Exception as e:
            print(f"Download Error: {e}")
            pass

    def download_all(self, assets):
        pass

    def action_pass(self):
        pass
    def action_save(self):
        pass
    def action_save_all(self):
        pass
    def open_preview(self):
        pass
    def quick_search(self, k):
        pass
    def load_next_asset(self):
        pass
    def load_image(self, u):
        pass

                                                                                
                                   
                                                                                
                                     
                   
                                                                 
                                                      
                                                                                
                                                                                
                                                                                
                        
                                                                                
                                                  
                                                                                
class ScheduleManager:
    def __init__(self, logger_func=None):
        self.schedule_file = os.path.join("config", "schedule.json")
        self.logger = logger_func
        self.ensure_file()

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(f"[ScheduleManager] {msg}")

    def ensure_file(self):
        if not os.path.exists(self.schedule_file):
            with open(self.schedule_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def load_schedule(self):
        try:
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_schedule(self, data):
        try:
            with open(self.schedule_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log(f"Error saving schedule: {e}")

    def generate_monthly_plan(self, start_day, available_files, times_per_day=["10:00", "14:00", "19:00"]):
        """
        Generates a schedule continuously starting from start_day of current month,
        rolling over to next months/years until files are exhausted.
        available_files: List of filenames in DIRS['output']
        times_per_day: List of time strings "HH:MM"
        """
        now = datetime.now()
        
                              
                                                                     
                                                                                                              
                                                                     
        try:
            current_date = datetime(now.year, now.month, int(start_day))
        except ValueError:
                                                                       
            current_date = now

        schedule = self.load_schedule()
        files_pool = list(available_files)
        random.shuffle(files_pool)                      
        
        assigned_count = 0
        final_date_str = ""
        
                                                                          
        safety_limit = 365
        days_processed = 0
        
        while files_pool and days_processed < safety_limit:
            date_str = current_date.strftime("%Y-%m-%d")
            
            day_slots = []
            for t_str in times_per_day:
                if not files_pool:
                    break
                
                file_to_assign = files_pool.pop(0)
                day_slots.append({
                    "time": t_str,
                    "file": file_to_assign,
                    "status": "pending"
                })
                assigned_count += 1
            
            if day_slots:
                                                                                             
                schedule[date_str] = day_slots
                final_date_str = date_str
                
            current_date += timedelta(days=1)
            days_processed += 1

        self.save_schedule(schedule)
        return assigned_count, final_date_str

    def get_next_pending_slot(self):
        """
        Returns (date_str, slot_data) for the earliest 'pending' slot of TODAY.
        """
        schedule = self.load_schedule()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        if date_str not in schedule:
            return None, None
            
        slots = schedule[date_str]
                                         
        slots.sort(key=lambda x: x["time"])
        
        for slot in slots:
            if slot["status"] == "pending":
                return date_str, slot
        
        return None, None

    def update_slot_status(self, date_str, time_str, new_status):
        schedule = self.load_schedule()
        if date_str in schedule:
            for slot in schedule[date_str]:
                if slot["time"] == time_str:
                    slot["status"] = new_status
                    self.save_schedule(schedule)
                    return True
        return False
            
        slots = schedule[date_str]
                            
        slots.sort(key=lambda x: x["time"])
        
        for slot in slots:
            if slot["status"] == "pending":
                            
                h, m = map(int, slot["time"].split(":"))
                slot_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                
                                
                delta = (slot_time - now).total_seconds()
                
                                                                  
                                                                                                            
                                                                           
                                                            
                
                return date_str, slot, delta
                
        return None, None, None

    def mark_as_posted(self, date_str, filename):
        schedule = self.load_schedule()
        if date_str in schedule:
            changed = False
            for slot in schedule[date_str]:
                if slot["file"] == filename and slot["status"] == "pending":
                    slot["status"] = "posted"
                    changed = True
                    break                    
            if changed:
                self.save_schedule(schedule)

class CalendarView(ctk.CTkToplevel):
    def __init__(self, parent, schedule_manager):
        super().__init__(parent)
        self.title("Monthly Schedule Calendar")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.minsize(900, 600)
        self.schedule_manager = schedule_manager
        self.parent = parent
        
                       
        self.update_idletasks()
        width = 1100
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.current_date = datetime.now()
        self.selected_date = None
        
        self.setup_ui()
        self.refresh_calendar()
        
                        
        self.lift()
        self.focus_force()
        self.grab_set()

    def setup_ui(self):
                                                       
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
                                      
        self.frame_cal = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cal.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
                                   
        self.head_frame = ctk.CTkFrame(self.frame_cal, fg_color="transparent")
        self.head_frame.pack(fill="x", pady=(0, 10))
        
        self.btn_prev = ctk.CTkButton(self.head_frame, text="<", width=40, command=self.prev_month, fg_color="#444")
        self.btn_prev.pack(side="left")
        
        self.lbl_month = ctk.CTkLabel(self.head_frame, text="Month Year", font=("Roboto", 16, "bold"))
        self.lbl_month.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.head_frame, text=">", width=40, command=self.next_month, fg_color="#444")
        self.btn_next.pack(side="right")
        
                                    
        self.days_frame = ctk.CTkFrame(self.frame_cal, fg_color="transparent")
        self.days_frame.pack(fill="x", pady=(0, 5))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days):
            self.days_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(self.days_frame, text=d, font=("Roboto", 11, "bold"), text_color="gray").grid(row=0, column=i, sticky="ew")
            
                             
        self.grid_frame = ctk.CTkFrame(self.frame_cal, fg_color="#1a1a1a")
        self.grid_frame.pack(fill="both", expand=True)
                            
        for i in range(7): self.grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(6): self.grid_frame.grid_rowconfigure(i, weight=1)
        
                                      
        self.frame_details = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=0)
        self.frame_details.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_details, text="Details", font=("Roboto", 14, "bold")).pack(pady=10, padx=10)
        
        self.lbl_sel_date = ctk.CTkLabel(self.frame_details, text="Select date", font=("Roboto", 12), text_color="#aaa")
        self.lbl_sel_date.pack(pady=(0, 10))
        
        self.scroll_details = ctk.CTkScrollableFrame(self.frame_details, fg_color="transparent")
        self.scroll_details.pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_calendar(self):
                             
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        year = self.current_date.year
        month = self.current_date.month
        
        self.lbl_month.configure(text=f"{calendar.month_name[month]} {year}")
        
                             
        cal = calendar.monthcalendar(year, month)
        schedule_data = self.schedule_manager.load_schedule()
        
        row = 0
        for week in cal:
            for col, day in enumerate(week):
                if day != 0:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    
                                            
                    cell_frame = ctk.CTkFrame(self.grid_frame, fg_color="#222", corner_radius=5)
                    cell_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                    
                                         
                    cell_frame.bind("<Button-1>", lambda e, d=date_str: self.show_details(d))
                    
                                
                    lbl_day = ctk.CTkLabel(cell_frame, text=str(day), font=("Roboto", 10, "bold"))
                    lbl_day.place(relx=0.1, rely=0.1, anchor="nw")
                    lbl_day.bind("<Button-1>", lambda e, d=date_str: self.show_details(d))
                    
                                      
                    events = schedule_data.get(date_str, [])
                    if events:
                        count = len(events)
                                                
                        has_pending = any(e.get('status') == 'pending' for e in events)
                        has_error = any('error' in e.get('status', '').lower() or 'failed' in e.get('status', '').lower() for e in events)
                        has_posted = any(e.get('status') == 'posted' for e in events)
                        
                        indicator_color = "#555"
                        if has_error: indicator_color = "#D32F2F"
                        elif has_pending: indicator_color = "#1976D2"
                        elif has_posted: indicator_color = "#388E3C"
                        
                                                        
                        lbl_count = ctk.CTkLabel(cell_frame, text=f"{count}", font=("Roboto", 9), 
                                                 text_color="white", fg_color=indicator_color, corner_radius=6, width=16, height=16)
                        lbl_count.place(relx=0.5, rely=0.5, anchor="center")
                        lbl_count.bind("<Button-1>", lambda e, d=date_str: self.show_details(d))
                        
                else:
                                
                    ctk.CTkLabel(self.grid_frame, text="").grid(row=row, column=col)
            row += 1
            
    def show_details(self, date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            self.lbl_sel_date.configure(text=date_obj.strftime("%d %b %Y"))
        except:
            self.lbl_sel_date.configure(text=date_str)
            
        self.selected_date = date_str
        
                    
        for widget in self.scroll_details.winfo_children():
            widget.destroy()
            
        schedule_data = self.schedule_manager.load_schedule()
        events = schedule_data.get(date_str, [])
        
        if not events:
            ctk.CTkLabel(self.scroll_details, text="No events", text_color="gray", font=("Roboto", 11)).pack(pady=10)
            return
            
                      
        events.sort(key=lambda x: x.get('time', '00:00'))
        
        for ev in events:
            card = ctk.CTkFrame(self.scroll_details, fg_color="#333")
            card.pack(fill="x", pady=3)
            
                           
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(top_row, text=ev.get('time', '??:??'), font=("Roboto", 12, "bold")).pack(side="left")
            
            status = ev.get('status', 'pending')
            status_color = "#1976D2"       
            if status == 'posted': status_color = "#388E3C"        
            elif 'error' in status.lower() or 'failed' in status.lower(): status_color = "#D32F2F"      
            
            ctk.CTkLabel(top_row, text=status.upper(), font=("Roboto", 9, "bold"), text_color=status_color).pack(side="right")
            
                  
            file_path = ev.get('file', 'Unknown')
            ctk.CTkLabel(card, text=file_path, font=("Roboto", 10), text_color="#ccc", wraplength=480, anchor="w", justify="left").pack(fill="x", padx=5, pady=(0, 5))

    def prev_month(self):
        first = self.current_date.replace(day=1)
        prev_month = first - timedelta(days=1)
        self.current_date = prev_month
        self.refresh_calendar()

    def next_month(self):
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        next_month = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = next_month.replace(day=1)
        self.refresh_calendar()

class ContentGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
                              
        self.title("The Content Factory (Pro) | Release v1.0")
        self.geometry("1200x850")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(os.path.join(ASSETS_DIR, "images", "catface.ico"))
        except Exception as e:
            print(f"Could not load icon: {e}")

                               
        self.color_bg = "#1e1e1e"
        self.color_card = "#252525"
        self.color_accent = "#E91E63"
        self.color_accent_hover = "#C2185B"
        self.color_text = "#FFFFFF"
        self.color_input_bg = "#303030"
        
                               
        self.settings = self.load_settings()
        self.last_generated_content = {"quote": "", "hook": "", "file": ""}
        self.schedule_manager = ScheduleManager(self.log_social_activity)
        self.is_generating = False
        self.current_generating_file = None

        self.ui_callback_queue = []
        self.ui_queue_lock = threading.Lock()
        self._tk_after = super().after
        self._tk_after(100, self.process_ui_queue)
        self.after = self.safe_after
        
                           
        self.main_tabs = ctk.CTkTabview(self)
        self.main_tabs.pack(fill="both", expand=True)
        self.tab_gen = self.main_tabs.add("Generator")
        self.tab_social = self.main_tabs.add("Auto Post")
        self.tab_dl = self.main_tabs.add("Source Download")
        self.tab_tools = self.main_tabs.add("AI Write")
        self.after(2000, self.auto_load_latest_preview)

                                                                                
                                   
                                                                                
        self.tab_gen.grid_columnconfigure(0, weight=4)
        self.tab_gen.grid_columnconfigure(1, weight=6)
        self.tab_gen.grid_rowconfigure(0, weight=0)
        self.tab_gen.grid_rowconfigure(1, weight=1)
        self.tab_gen.grid_rowconfigure(2, weight=0)

        self.header_frame = ctk.CTkFrame(self.tab_gen, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=5)

        self.lbl_title = ctk.CTkLabel(self.header_frame, text="Content Generator", font=("Helvetica", 18, "bold"), text_color=self.color_accent)
        self.lbl_title.pack(side="left")

        self.label_status = ctk.CTkLabel(self.header_frame, text="Ready", font=("Helvetica", 11), text_color="gray")
        self.label_status.pack(side="right", padx=10)

        self.lbl_generated_count = ctk.CTkLabel(self.header_frame, text="Generated: 0 / 0", font=("Helvetica", 12, "bold"), text_color="#4CAF50")
        self.lbl_generated_count.pack(side="right", padx=5)

        self.lbl_info = ctk.CTkLabel(self, text="", font=("Helvetica", 16), fg_color="#333", corner_radius=10)

        self.panel_left = ctk.CTkFrame(self.tab_gen, fg_color=self.color_card, corner_radius=15)
        self.panel_left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=5)

        self.panel_left.grid_columnconfigure(0, weight=1)

        frame_brand = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_brand.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))

        ctk.CTkLabel(frame_brand, text="BRANDING", font=("Roboto", 13, "bold"), text_color=self.color_accent).pack(anchor="w", pady=(0, 5))

        row_b1 = ctk.CTkFrame(frame_brand, fg_color="transparent")
        row_b1.pack(fill="x", pady=5)

        self.combo_font = ctk.CTkComboBox(row_b1, values=self.get_font_list(), fg_color=self.color_input_bg, button_color=self.color_accent, height=32, font=("Roboto", 12))
        self.combo_font.pack(side="left", fill="x", expand=True, padx=(0, 5))
        if self.settings.get("font") in self.combo_font._values:
            self.combo_font.set(self.settings.get("font"))

        self.var_random_font = ctk.BooleanVar(value=self.settings.get("random_font", False))
        self.chk_random_font = ctk.CTkCheckBox(row_b1, text="Random Font", variable=self.var_random_font, width=60, font=("Roboto", 12))
        self.chk_random_font.pack(side="right", padx=5)

        self.frame_brand_input = ctk.CTkFrame(frame_brand, fg_color="transparent")
        self.frame_brand_input.pack(fill="x", pady=5)
        
        self.frame_brand_input.grid_columnconfigure(0, weight=1)
        self.frame_brand_input.grid_columnconfigure(1, weight=1)

        self.entry_tiktok = ctk.CTkEntry(self.frame_brand_input, placeholder_text="TikTok: @YourChannel", fg_color=self.color_input_bg, height=35, font=("Roboto", 12))
        self.entry_tiktok.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 5))
        self.entry_tiktok.insert(0, self.settings.get("tiktok_channel_name", self.settings.get("channel_name", "")))
        
        self.entry_ig = ctk.CTkEntry(self.frame_brand_input, placeholder_text="IG: @YourIG", fg_color=self.color_input_bg, height=35, font=("Roboto", 12))
        self.entry_ig.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 5))
        self.entry_ig.insert(0, self.settings.get("ig_channel_name", ""))

        frame_content = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_content.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        frame_content.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_content, text="CONTENT", font=("Roboto", 13, "bold"), text_color=self.color_accent).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        ctk.CTkLabel(frame_content, text="Time (sec):", font=("Roboto", 12)).grid(row=1, column=0, sticky="w", pady=5)
        
        sub_frame_dur = ctk.CTkFrame(frame_content, fg_color="transparent")
        sub_frame_dur.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        self.combo_duration = ctk.CTkComboBox(sub_frame_dur, width=80, values=["15s", "30s", "45s", "60s"], fg_color=self.color_input_bg, button_color=self.color_accent, height=32, font=("Roboto", 12))
        self.combo_duration.pack(side="left")
        saved_duration = _parse_duration_seconds(self.settings.get("duration", 15))
        self.combo_duration.set(f"{saved_duration}s")
        
        ctk.CTkLabel(sub_frame_dur, text="Qty:", font=("Roboto", 12)).pack(side="left", padx=(15, 5))
        self.entry_count = ctk.CTkEntry(sub_frame_dur, width=60, fg_color=self.color_input_bg, height=32, font=("Roboto", 12))
        self.entry_count.pack(side="left")
        self.entry_count.insert(0, str(self.settings.get("count", "1")))

        ctk.CTkLabel(frame_content, text="Volume:", font=("Roboto", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.slider_volume = ctk.CTkSlider(frame_content, from_=0, to=1.0, number_of_steps=20, button_color=self.color_accent, progress_color=self.color_accent, height=18, command=self.update_volume_label)
        self.slider_volume.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.slider_volume.set(self.settings.get("volume", 0.5))
        
        self.lbl_volume_value = ctk.CTkLabel(frame_content, text=f"{int(self.slider_volume.get()*100)}%", font=("Roboto", 12), width=35)
        self.lbl_volume_value.grid(row=2, column=2, sticky="w", padx=(0, 5))

        ctk.CTkLabel(frame_content, text="Filter:", font=("Roboto", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.combo_filter = ctk.CTkComboBox(frame_content, values=["None", "Darken (Cinematic)", "Black & White", "Sepia", "Vignette", "Warm Tone", "Cool Tone", "Soft Blur", "High Contrast"], fg_color=self.color_input_bg, button_color=self.color_accent, height=32, font=("Roboto", 12))
        self.combo_filter.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.combo_filter.set(self.settings.get("filter", "None"))

        ctk.CTkLabel(frame_content, text="Theme:", font=("Roboto", 12)).grid(row=4, column=0, sticky="w", pady=5)
        
                                 
        try:
            with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                q_data = json.load(f)
                theme_list = ["All / Random"] + list(q_data.keys())
        except:
            theme_list = ["All / Random", "love", "sad", "motivation", "self_development", "life"]

        self.combo_theme = ctk.CTkComboBox(frame_content, values=theme_list, fg_color=self.color_input_bg, button_color=self.color_accent, height=32, font=("Roboto", 12))
        self.combo_theme.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        self.combo_theme.set(self.settings.get("theme", "All / Random"))
        ctk.CTkLabel(self.panel_left, text="SETTINGS", font=("Roboto", 13, "bold"), text_color=self.color_accent).grid(row=2, column=0, sticky="w", padx=15, pady=(10, 5))
                                                             
        self.panel_left.grid_rowconfigure(3, weight=1)
        frame_opts = ctk.CTkScrollableFrame(self.panel_left, fg_color="transparent")
        frame_opts.grid(row=3, column=0, sticky="nsew", padx=15, pady=0)
        frame_opts.grid_columnconfigure(0, weight=1)
        frame_opts.grid_columnconfigure(1, weight=1)

        self.var_fade_in = ctk.BooleanVar(value=self.settings.get("fade_in", True))
        ctk.CTkCheckBox(frame_opts, text="Fade In", variable=self.var_fade_in, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)

        self.var_fade_out = ctk.BooleanVar(value=self.settings.get("fade_out", True))
        ctk.CTkCheckBox(frame_opts, text="Fade Out", variable=self.var_fade_out, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=0, column=1, sticky="w", padx=(5, 0), pady=5)

        self.var_prog_bar = ctk.BooleanVar(value=self.settings.get("progress_bar", True))
        ctk.CTkCheckBox(frame_opts, text="Progress Bar", variable=self.var_prog_bar, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)

        self.var_stretch = ctk.BooleanVar(value=self.settings.get("stretch_video", False))
        ctk.CTkCheckBox(frame_opts, text="Stretch Video", variable=self.var_stretch, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=1, column=1, sticky="w", padx=(5, 0), pady=5)

        self.var_dynamic_zoom = ctk.BooleanVar(value=self.settings.get("dynamic_zoom", False))
        ctk.CTkCheckBox(frame_opts, text="Dynamic Zoom", variable=self.var_dynamic_zoom, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=2, column=0, sticky="w", padx=(0, 5), pady=5)

        self.var_smart_shadow = ctk.BooleanVar(value=self.settings.get("smart_shadow", True))
        ctk.CTkCheckBox(frame_opts, text="Smart Shadow", variable=self.var_smart_shadow, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=2, column=1, sticky="w", padx=(5, 0), pady=5)
        
        self.var_mood_random = ctk.BooleanVar(value=self.settings.get("mood_random", False))
        ctk.CTkCheckBox(frame_opts, text="Auto Mood", variable=self.var_mood_random, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=3, column=0, sticky="w", padx=(0, 5), pady=5)
        
        self.var_tts = ctk.BooleanVar(value=self.settings.get("tts_enabled", False))
        ctk.CTkCheckBox(frame_opts, text="Enable AI Voice (Demo)", variable=self.var_tts, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=3, column=1, sticky="w", padx=(5, 0), pady=5)

        self.var_shutdown = ctk.BooleanVar(value=self.settings.get("auto_shutdown", False))
        self.chk_shutdown = ctk.CTkCheckBox(frame_opts, text="Shutdown Done", variable=self.var_shutdown, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20)
        self.chk_shutdown.grid(row=4, column=0, sticky="w", padx=(0, 5), pady=5)

        self.var_backdrop = ctk.BooleanVar(value=self.settings.get("text_backdrop", False))
        ctk.CTkCheckBox(frame_opts, text="Text Backdrop", variable=self.var_backdrop, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=4, column=1, sticky="w", padx=(5, 0), pady=5)
        
        self.var_show_hook = ctk.BooleanVar(value=self.settings.get("show_hook_text", True))
        ctk.CTkCheckBox(frame_opts, text="Show Hook Text", variable=self.var_show_hook, fg_color=self.color_accent, font=("Roboto", 11), checkbox_height=20, checkbox_width=20).grid(row=5, column=0, sticky="w", padx=(0, 5), pady=5)
        self.setup_smart_tools_tab()
        
        self.panel_right = ctk.CTkFrame(self.tab_gen, fg_color=self.color_card, corner_radius=15)
        self.panel_right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=5)

        self.panel_right.grid_columnconfigure(0, weight=1)
        self.panel_right.grid_rowconfigure(0, weight=1)
        self.panel_right.grid_rowconfigure(1, weight=0)

        self.preview_box = ctk.CTkFrame(self.panel_right, fg_color="#101010", corner_radius=10)
        self.preview_box.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.lbl_preview_img = ctk.CTkLabel(self.preview_box, text="Click 'Preview'", text_color="#444", font=("Roboto", 14))
        self.lbl_preview_img.place(relx=0.5, rely=0.5, anchor="center")

        btn_frame = ctk.CTkFrame(self.panel_right, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        self.btn_preview = ctk.CTkButton(btn_frame, text="PREVIEW", command=lambda: self.generate_preview(True), height=45, fg_color="#333", hover_color="#444", corner_radius=8, font=("Roboto", 12, "bold"))
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.setup_bindings()

        self.btn_generate = ctk.CTkButton(btn_frame, text="GENERATE", command=self.start_generation, height=45, fg_color=self.color_accent, hover_color=self.color_accent_hover, corner_radius=8, font=("Roboto", 14, "bold"))
        self.btn_generate.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.panel_footer = ctk.CTkFrame(self.tab_gen, fg_color="transparent")
        self.panel_footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))

        self.progress = ctk.CTkProgressBar(self.panel_footer, height=6, progress_color=self.color_accent)
        self.progress.pack(fill="x", pady=(0, 5))
        self.progress.set(0)

        self.log_textbox = ctk.CTkTextbox(self.panel_footer, height=150, fg_color="#121212", text_color="#888", font=("Consolas", 12), corner_radius=8)
        self.log_textbox.pack(fill="x")
        self.log_textbox.configure(state="disabled")

        self.downloader = AssetDownloader(self.tab_dl, self.settings, self)
        self.downloader.pack(fill="both", expand=True)

        self.tab_social.grid_columnconfigure(0, weight=1)
        self.tab_social.grid_columnconfigure(1, weight=2)
        self.tab_social.grid_columnconfigure(2, weight=2)
        self.tab_social.grid_rowconfigure(0, weight=1)

                                   
        self.soc_left = ctk.CTkFrame(self.tab_social, fg_color=self.color_card, corner_radius=15)
        self.soc_left.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        self.soc_left.grid_rowconfigure(3, weight=1)                     

        self.lbl_queue_header = ctk.CTkLabel(self.soc_left, text="Video Queue (0)", font=("Roboto", 16, "bold"))
        self.lbl_queue_header.grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=15, sticky="w")
        
                                
        _, _, quotes_data, _ = self.load_available_assets()
        theme_keys = sorted([k for k in quotes_data.keys() if k != "default"])
        filter_values = ["All"] + theme_keys
        
        self.combo_queue_filter = ctk.CTkOptionMenu(self.soc_left, values=filter_values, command=lambda x: self.refresh_video_list())
        self.combo_queue_filter.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        self.combo_queue_filter.set("All")

        queue_tools = ctk.CTkFrame(self.soc_left, fg_color="transparent")
        queue_tools.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        ctk.CTkButton(queue_tools, text="All", width=40, height=24, fg_color="#444", hover_color="#555", font=("Roboto", 11), command=self.select_all_queue).pack(side="left", padx=2)
        ctk.CTkButton(queue_tools, text="None", width=45, height=24, fg_color="#444", hover_color="#555", font=("Roboto", 11), command=lambda: [v.set(False) for _, v in self.queue_vars]).pack(side="left", padx=2)
        ctk.CTkButton(queue_tools, text="↻", width=30, height=24, fg_color="#444", hover_color="#555", font=("Roboto", 12), command=self.refresh_video_list).pack(side="right", padx=2)

        self.queue_scroll = ctk.CTkScrollableFrame(self.soc_left, fg_color=self.color_input_bg)
        self.queue_scroll.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        self.queue_vars = []

        sel_frame = ctk.CTkFrame(self.soc_left, fg_color="transparent")
        sel_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.entry_sel_qty = ctk.CTkEntry(sel_frame, width=40, height=28, placeholder_text="#", fg_color=self.color_input_bg, font=("Roboto", 12))
        self.entry_sel_qty.pack(side="left", padx=(5, 5))
        ctk.CTkButton(sel_frame, text="Select Top", command=self.select_videos_in_queue_by_quantity, height=28, fg_color="#444", hover_color="#555", font=("Roboto", 12)).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(sel_frame, text="Random", command=self.randomly_select_videos_in_queue, height=28, fg_color="#444", hover_color="#555", font=("Roboto", 12)).pack(side="left", padx=2, expand=True, fill="x")

                                  
        self.soc_center = ctk.CTkFrame(self.tab_social, fg_color="transparent")
        self.soc_center.grid(row=0, column=1, sticky="nsew", padx=5, pady=15)
        self.soc_center.grid_columnconfigure(0, weight=1)
        
                                       
        self.soc_center.grid_rowconfigure(0, weight=1) 
        
        log_panel = ctk.CTkFrame(self.soc_center, fg_color=self.color_card, corner_radius=15)
        log_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        ctk.CTkLabel(log_panel, text="Activity Log", font=("Roboto", 14, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.soc_log_box = ctk.CTkTextbox(log_panel, font=("Consolas", 11), fg_color="#111", text_color="#0f0", height=100)                 
        self.soc_log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

                        
        self.soc_center.grid_rowconfigure(1, weight=0)
        
        action_panel = ctk.CTkFrame(self.soc_center, fg_color=self.color_card, corner_radius=15)
        action_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.btn_start_post = ctk.CTkButton(action_panel, text="🚀 START AUTO-POST", command=self.start_autopost_process, height=50, fg_color=self.color_accent, hover_color=self.color_accent_hover, font=("Roboto", 16, "bold"))
        self.btn_start_post.pack(fill="x", padx=15, pady=(15, 10))
        
        login_frame = ctk.CTkFrame(action_panel, fg_color="transparent")
        login_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.btn_login_helper = ctk.CTkButton(login_frame, text="🔑 Login Accounts", command=self.open_login_browser, height=32, fg_color="#444", hover_color="#555", font=("Roboto", 12, "bold"))
        self.btn_login_helper.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_close_browser = ctk.CTkButton(login_frame, text="❌ Close Browser", command=self.close_browser, height=32, fg_color="#D32F2F", hover_color="#B71C1C", font=("Roboto", 12, "bold"))
        self.btn_close_browser.pack(side="right", fill="x", expand=True, padx=(5, 0))

                                             
        self.soc_center.grid_rowconfigure(2, weight=2)                          
        
        config_panel = ctk.CTkFrame(self.soc_center, fg_color=self.color_card, corner_radius=15)
        config_panel.grid(row=2, column=0, sticky="nsew")
        config_panel.grid_columnconfigure(0, weight=1)
        config_panel.grid_columnconfigure(1, weight=1)
        
                
        head_frame = ctk.CTkFrame(config_panel, fg_color="transparent")
        head_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=15)
        ctk.CTkLabel(head_frame, text="Auto-Post Settings", font=("Roboto", 16, "bold")).pack(side="left")
        self.lbl_post_count = ctk.CTkLabel(head_frame, text="Today: 0", font=("Roboto", 12, "bold"), text_color="#aaa")
        self.lbl_post_count.pack(side="right")

                          
        plat_label = ctk.CTkLabel(config_panel, text="Target Platforms:", font=("Roboto", 12, "bold"), text_color="gray")
        plat_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 5))

        self.var_tiktok = ctk.BooleanVar(value=True)
        self.var_ig = ctk.BooleanVar(value=True)
        self.var_yt = ctk.BooleanVar(value=False)
        self.var_fb = ctk.BooleanVar(value=True)

        plat_frame = ctk.CTkFrame(config_panel, fg_color=self.color_input_bg, corner_radius=8)
        plat_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        ctk.CTkCheckBox(plat_frame, text="TikTok", variable=self.var_tiktok, font=("Roboto", 12)).pack(side="left", padx=10, pady=10, expand=True)
        ctk.CTkCheckBox(plat_frame, text="Instagram", variable=self.var_ig, font=("Roboto", 12)).pack(side="left", padx=10, pady=10, expand=True)
        ctk.CTkCheckBox(plat_frame, text="Facebook", variable=self.var_fb, font=("Roboto", 12)).pack(side="left", padx=10, pady=10, expand=True)
        
                         
        theme_label = ctk.CTkLabel(config_panel, text="Target Theme:", font=("Roboto", 12, "bold"), text_color="gray")
        theme_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 5))
        
        self.combo_autopost_theme = ctk.CTkOptionMenu(config_panel, values=["All / Random"] + theme_keys)
        self.combo_autopost_theme.grid(row=4, column=0, sticky="ew", padx=(15, 5), pady=(0, 15))
        self.combo_autopost_theme.set("All / Random")

        self.chk_autopost_random = ctk.CTkCheckBox(config_panel, text="Random Theme", font=("Roboto", 12))
        self.chk_autopost_random.grid(row=4, column=1, sticky="w", padx=5, pady=(0, 15))
        
                                        
        ctk.CTkLabel(config_panel, text="Posting Mode:", font=("Roboto", 12, "bold"), text_color="gray").grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 5))
        
        mode_frame = ctk.CTkFrame(config_panel, fg_color="transparent")
        mode_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        self.var_post_mode = ctk.StringVar(value="Interval")
        
                                        
        self.radio_mode_interval = ctk.CTkRadioButton(mode_frame, text="Queue (Interval)", variable=self.var_post_mode, value="Interval", font=("Roboto", 12))
        self.radio_mode_interval.pack(side="left", padx=(0, 15))
        
                                     
        self.radio_mode_schedule = ctk.CTkRadioButton(mode_frame, text="Schedule (Time)", variable=self.var_post_mode, value="Schedule", font=("Roboto", 12))
        self.radio_mode_schedule.pack(side="left")

                         
        sett_label = ctk.CTkLabel(config_panel, text="Limits & Delays:", font=("Roboto", 12, "bold"), text_color="gray")
        sett_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 5))

        sett_frame = ctk.CTkFrame(config_panel, fg_color="transparent")
        sett_frame.grid(row=8, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(sett_frame, text="Delay (min):", font=("Roboto", 12)).pack(side="left", padx=(0,5))
        self.entry_interval = ctk.CTkEntry(sett_frame, width=50, fg_color=self.color_input_bg, font=("Roboto", 12))
        self.entry_interval.pack(side="left")
        self.entry_interval.insert(0, "180")
        
        self.var_limit_enabled = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sett_frame, text="Limit Upload", variable=self.var_limit_enabled, width=60, font=("Roboto", 12)).pack(side="left", padx=(15, 5))
        self.entry_daily_limit = ctk.CTkEntry(sett_frame, width=50, fg_color=self.color_input_bg, font=("Roboto", 12))
        self.entry_daily_limit.pack(side="left")
        self.entry_daily_limit.insert(0, str(self.settings.get("daily_post_limit", 5)))
        self.entry_daily_limit.bind("<KeyRelease>", lambda e: self.update_post_count_label())
        
                 
        self.var_headless = ctk.BooleanVar(value=self.settings.get("headless_browser", False))
        ctk.CTkCheckBox(sett_frame, text="Hide Browser", variable=self.var_headless, font=("Roboto", 12)).pack(side="right")

                                          
        sched_label = ctk.CTkLabel(config_panel, text="Monthly Schedule:", font=("Roboto", 12, "bold"), text_color="gray")
        sched_label.grid(row=9, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5))

        sched_frame = ctk.CTkFrame(config_panel, fg_color="transparent")
        sched_frame.grid(row=10, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkLabel(sched_frame, text="Start Day:", font=("Roboto", 12)).pack(side="left", padx=(0, 5))
        self.entry_sched_day = ctk.CTkEntry(sched_frame, width=40, fg_color=self.color_input_bg, font=("Roboto", 12))
        self.entry_sched_day.pack(side="left")
        self.entry_sched_day.insert(0, str(datetime.now().day))

        ctk.CTkButton(sched_frame, text="Generate Plan", command=self.on_click_generate_schedule, height=28, fg_color="#555", hover_color="#666", width=100).pack(side="left", padx=10)
        ctk.CTkButton(sched_frame, text="View Plan", command=self.on_click_view_schedule, height=28, fg_color="#333", hover_color="#444", width=80).pack(side="left")
        
        self.soc_right = ctk.CTkFrame(self.tab_social, fg_color=self.color_card, corner_radius=15)
        self.soc_right.grid(row=0, column=2, sticky="nsew", padx=(5, 15), pady=15)
        
        ctk.CTkLabel(self.soc_right, text="Live Preview", font=("Roboto", 16, "bold")).pack(pady=15)
        self.soc_preview_frame = ctk.CTkFrame(self.soc_right, fg_color="#000")
        self.soc_preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.video_player = VideoPlayerFrame(self.soc_preview_frame)
        self.video_player.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.soc_right, text="▶ Play Selected", command=self.preview_selected_video_thumbnail, height=40, fg_color=self.color_accent, hover_color=self.color_accent_hover, font=("Roboto", 14, "bold")).pack(fill="x", padx=15, pady=(0, 15))
        self.post_running = False
        self.active_automator = None
        self.initialize_file_structure()
        self.update_post_count_label()
        self.after(2000, self.consolidate_old_json_files)
        self.refresh_video_list()
        self.after(1000, self.auto_load_latest_preview)
        self.after(1500, lambda: self.generate_preview(True))

    def setup_bindings(self):
        self.combo_font.configure(command=lambda x: self.auto_preview())
        self.combo_filter.configure(command=lambda x: self.auto_preview())
        self.combo_duration.configure(command=lambda x: self.auto_preview())
        self.entry_tiktok.bind("<KeyRelease>", lambda e: self.auto_preview())
        self.entry_ig.bind("<KeyRelease>", lambda e: self.auto_preview())
        
        def on_vol_change(x):
            self.update_volume_label(x)
            self.auto_preview()
            
        self.slider_volume.configure(command=on_vol_change)
        
        if hasattr(self, 'combo_theme'):
            self.combo_theme.configure(command=lambda x: self.auto_preview())

    def update_volume_label(self, value):
        self.lbl_volume_value.configure(text=f"{int(float(value)*100)}%")

    def open_settings(self):
                                                 
        self.log("Settings menu opened")

    def auto_preview(self):
        if hasattr(self, '_preview_timer') and self._preview_timer:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(500, lambda: self.generate_preview(False))

                                                                                    
                                     
                                                                                    
                                                     
                                                                        
                                                                                    
    def setup_smart_tools_tab(self):
        self.tab_tools.grid_columnconfigure(0, weight=1)
        self.tab_tools.grid_columnconfigure(1, weight=1)
        self.tab_tools.grid_rowconfigure(0, weight=1)
        self.card_assets = ctk.CTkFrame(self.tab_tools, fg_color=self.color_card, corner_radius=15)
        self.card_assets.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.card_assets.grid_rowconfigure(1, weight=1)
        self.card_assets.grid_columnconfigure(0, weight=1)
        header_frame_am = ctk.CTkFrame(self.card_assets, fg_color="transparent")
        header_frame_am.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        ctk.CTkLabel(header_frame_am, text="Asset Manager", font=("Roboto", 20, "bold")).pack(side="left")
        self.tabview_am = ctk.CTkTabview(self.card_assets, fg_color="transparent")
        self.tabview_am.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        tab_quotes = self.tabview_am.add("Quotes")
        tab_hooks = self.tabview_am.add("Hooks")
        def load_quotes_from_file():
            try:
                with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list): return data
                    elif isinstance(data, dict):
                        all_lines = []
                        for k, v in data.items():
                            all_lines.append(f"[{k}]")
                            if isinstance(v, list): all_lines.extend(v)
                            all_lines.append("")
                        return all_lines
                    return []
            except: return []

        def save_quotes_to_file(lines):
            try:
                has_sections = any(line.strip().startswith("[") and line.strip().endswith("]") for line in lines)
                
                if has_sections:
                    new_data = {}
                    current_section = "Love"
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        
                        if line.startswith("[") and line.endswith("]"):
                            current_section = line[1:-1]
                            if current_section not in new_data:
                                new_data[current_section] = []
                        else:
                            if current_section not in new_data:
                                new_data[current_section] = []
                            new_data[current_section].append(line)
                    
                    with open(DIRS["quotes"], "w", encoding="utf-8") as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=4)
                else:
                    with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        data = lines
                    else:
                        key = "Love"
                        if key not in data:
                            keys = list(data.keys())
                            if keys: key = keys[0]
                        data[key] = lines
                        
                    with open(DIRS["quotes"], "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                self.log("Quotes updated.")
                self.lbl_info.configure(text="Quotes Saved Successfully!", text_color="#4CAF50")
                self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
                self.after(2000, lambda: self.lbl_info.place_forget())
            except Exception as e:
                self.log(f"Error saving quotes: {e}")

        self.quotes_textbox = ctk.CTkTextbox(tab_quotes, height=400, font=("Consolas", 12), fg_color="#1a1a1a")
        self.quotes_textbox.pack(fill="both", expand=True, pady=(0, 10))
        
        current_quotes = load_quotes_from_file()
        self.quotes_textbox.insert("1.0", "\n".join(current_quotes))

        def save_quotes_click():
            content = self.quotes_textbox.get("1.0", "end").strip()
            new_list = [line for line in content.split("\n") if line.strip()]
            save_quotes_to_file(new_list)

        ctk.CTkButton(tab_quotes, text="💾 Save Quotes", command=save_quotes_click, fg_color=self.color_accent, height=40, font=("Roboto", 13, "bold")).pack(fill="x")
        def load_hooks_from_file():
            try:
                with open(DIRS["hooks"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list): return data
                    elif isinstance(data, dict):
                        all_lines = []
                        for k, v in data.items():
                            all_lines.append(f"[{k}]")
                            if isinstance(v, list): all_lines.extend(v)
                            all_lines.append("")
                        return all_lines
                    return []
            except: return []

        def save_hooks_to_file(lines):
            try:
                has_sections = any(line.strip().startswith("[") and line.strip().endswith("]") for line in lines)
                
                if has_sections:
                    new_data = {}
                    current_section = "Love"
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        
                        if line.startswith("[") and line.endswith("]"):
                            current_section = line[1:-1]
                            if current_section not in new_data:
                                new_data[current_section] = []
                        else:
                            if current_section not in new_data:
                                new_data[current_section] = []
                            new_data[current_section].append(line)
                    
                    with open(DIRS["hooks"], "w", encoding="utf-8") as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=4)
                else:
                    with open(DIRS["hooks"], "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        data = lines
                    else:
                        key = "Love"
                        if key not in data:
                            keys = list(data.keys())
                            if keys: key = keys[0]
                        data[key] = lines
    
                    with open(DIRS["hooks"], "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                self.log("Hooks updated.")
                self.lbl_info.configure(text="Hooks Saved Successfully!", text_color="#4CAF50")
                self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
                self.after(2000, lambda: self.lbl_info.place_forget())
            except Exception as e:
                self.log(f"Error saving hooks: {e}")

        self.hooks_textbox = ctk.CTkTextbox(tab_hooks, height=400, font=("Consolas", 12), fg_color="#1a1a1a")
        self.hooks_textbox.pack(fill="both", expand=True, pady=(0, 10))
        
        current_hooks = load_hooks_from_file()
        self.hooks_textbox.insert("1.0", "\n".join(current_hooks))

        def save_hooks_click():
            content = self.hooks_textbox.get("1.0", "end").strip()
            new_list = [line for line in content.split("\n") if line.strip()]
            save_hooks_to_file(new_list)

        ctk.CTkButton(tab_hooks, text="💾 Save Hooks", command=save_hooks_click, fg_color=self.color_accent, height=40, font=("Roboto", 13, "bold")).pack(fill="x")
        self.card_ai = ctk.CTkFrame(self.tab_tools, fg_color=self.color_card, corner_radius=15)
        self.card_ai.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.card_ai.grid_rowconfigure(3, weight=1)
        self.card_ai.grid_columnconfigure(0, weight=1)

                                 
        themes_list = ["Love", "Motivation", "Business", "Life", "Sad", "Dark", "Nature"]
        try:
            with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): themes_list = list(d.keys())
        except: pass

        header_frame_ai = ctk.CTkFrame(self.card_ai, fg_color="transparent")
        header_frame_ai.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        ctk.CTkLabel(header_frame_ai, text="AI Writer", font=("Roboto", 20, "bold")).pack(side="left")
        input_frame = ctk.CTkFrame(self.card_ai, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(input_frame, text="Theme:", font=("Roboto", 14)).pack(side="left", padx=(0, 5))
        self.combo_ai_theme = ctk.CTkComboBox(input_frame, values=themes_list, width=150, height=35)
        self.combo_ai_theme.pack(side="left", padx=(0, 10))
        if themes_list: self.combo_ai_theme.set(themes_list[0])

        ctk.CTkLabel(input_frame, text="Type:", font=("Roboto", 14)).pack(side="left", padx=(0, 5))
        self.combo_ai_type = ctk.CTkComboBox(input_frame, values=["Quotes", "Hooks"], width=100, height=35, state="readonly")
        self.combo_ai_type.pack(side="left", fill="x", expand=True)
        self.combo_ai_type.set("Quotes")

        def run_ai_tool():
            theme = self.combo_ai_theme.get()
            ctype = self.combo_ai_type.get()
            api_key = self.settings.get("groq_api_key", "")
            if not api_key:
                self.txt_ai_output.insert("end", "❌ Error: Please set Groq API Key in Settings.\n")
                return
            
            self.btn_ai_gen.configure(state="disabled", text="Generating...", fg_color="#555")
            
            def thread_target():
                lines = self.generate_ai_content(theme, ctype, api_key)
                self.after(0, lambda: finish_ai_tool(lines))
                
            threading.Thread(target=thread_target).start()
            
        def finish_ai_tool(lines):
            self.btn_ai_gen.configure(state="normal", text="✨ Generate Content", fg_color="#673AB7")
            if lines:
                self.txt_ai_output.delete("1.0", "end")
                for line in lines:
                    self.txt_ai_output.insert("end", line + "\n")
            else:
                self.txt_ai_output.insert("end", "❌ No content generated.\n")

        self.btn_ai_gen = ctk.CTkButton(self.card_ai, text="✨ Generate Content", command=run_ai_tool, fg_color="#673AB7", hover_color="#512DA8", height=45, font=("Roboto", 15, "bold"))
        self.btn_ai_gen.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.txt_ai_output = ctk.CTkTextbox(self.card_ai, height=200, font=("Consolas", 12), fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.txt_ai_output.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 15))

        def append_ai_to_manager():
            content = self.txt_ai_output.get("1.0", "end").strip()
            if not content: return
            
            theme = self.combo_ai_theme.get()
            ctype = self.combo_ai_type.get()
            
            target_textbox = self.quotes_textbox if ctype == "Quotes" else self.hooks_textbox
            
            current_text = target_textbox.get("1.0", "end").strip()
            new_lines = [line for line in content.split('\n') if line.strip()]
            
            if "[" in current_text and "]" in current_text:
                formatted_append = f"\n\n[{theme}]\n" + "\n".join(new_lines)
                target_textbox.insert("end", formatted_append)
            else:
                if current_text:
                    target_textbox.insert("end", "\n" + "\n".join(new_lines))
                else:
                    target_textbox.insert("1.0", "\n".join(new_lines))
            
            self.log(f"AI {ctype} moved to Asset Manager.")
            self.lbl_info.configure(text=f"Added to {ctype}!", text_color="#4CAF50")
            self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
            self.after(2000, lambda: self.lbl_info.place_forget())

        ctk.CTkButton(self.card_ai, text="⬇ Add to Asset Manager", command=append_ai_to_manager, fg_color="green", height=40, font=("Roboto", 13, "bold")).grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))

    def open_asset_manager_window(self):
        self.main_tabs.set("Smart Tools")

    def open_ai_writer_window(self):
        self.main_tabs.set("Smart Tools")


    def switch_to_asset_downloader_tab(self):
        self.main_tabs.set("Asset Downloader")

    def load_settings(self):
        default_settings = {
            "channel_name": "",
            "duration": "15",
            "font": "Default",
            "random_font": False,
            "volume": 0.5,
            "tts_enabled": False,
            "tts_voice": "th-TH-NiwatNeural",
            "text_backdrop": False,
            "backdrop_opacity": 0.4,
            "groq_api_key": "",
            "count": "1",
            "auto_shutdown": False,
            "logo_type": "Text",
            "logo_path": "",
            "fade_in": True,
            "fade_out": True,
            "progress_bar": True,
            "filter": "None",
            "pexels_key": "",
            "pixabay_key": "",
            "show_hook_text": True
        }
        if os.path.exists(DIRS["config"]):
            try:
                with open(DIRS["config"], "r") as f:
                    data = json.load(f)
                    default_settings.update(data)
            except:
                pass
        return default_settings

    def save_settings(self):
        self.settings.update({
            "tiktok_channel_name": self.entry_tiktok.get(),
            "ig_channel_name": self.entry_ig.get(),
            "channel_name": self.entry_tiktok.get(),
            "duration": self.combo_duration.get(),
            "font": self.combo_font.get(),
            "random_font": self.var_random_font.get(),
            "volume": self.slider_volume.get(),
            "count": self.entry_count.get(),
            "auto_shutdown": self.var_shutdown.get(),
            "fade_in": self.var_fade_in.get(),
            "fade_out": self.var_fade_out.get(),
            "progress_bar": self.var_prog_bar.get(),
            "filter": self.combo_filter.get(),
            "tts_enabled": self.var_tts.get(),
            "text_backdrop": self.var_backdrop.get(),
            "daily_post_limit": self.entry_daily_limit.get(),
            "headless_browser": self.var_headless.get(),
            "theme": self.combo_theme.get(),
            "show_hook_text": self.var_show_hook.get()
        })
        try:
            os.makedirs(os.path.dirname(DIRS["config"]), exist_ok=True)
            with open(DIRS["config"], "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.log(f"Error saving settings: {e}")

    def get_font_list(self):
        if not os.path.exists(DIRS["fonts"]):
            return ["Default"]
        fonts = [f for f in os.listdir(DIRS["fonts"]) if f.endswith(('.ttf', '.otf'))]
        return fonts if fonts else ["Default"]

    def queue_ui_callback(self, delay, callback, *args, **kwargs):
        execute_at = time.time() + delay / 1000.0
        with self.ui_queue_lock:
            heapq.heappush(self.ui_callback_queue, (execute_at, callback, args, kwargs))

    def process_ui_queue(self):
        due_callbacks = []
        now = time.time()
        with self.ui_queue_lock:
            while self.ui_callback_queue and self.ui_callback_queue[0][0] <= now:
                _, callback, args, kwargs = heapq.heappop(self.ui_callback_queue)
                due_callbacks.append((callback, args, kwargs))

        for callback, args, kwargs in due_callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                pass

        if self.winfo_exists():
            self._tk_after(50, self.process_ui_queue)

    def safe_after(self, delay, callback, *args, **kwargs):
        if threading.current_thread() == threading.main_thread():
            self._tk_after(delay, callback, *args, **kwargs)
        else:
            self.queue_ui_callback(delay, callback, *args, **kwargs)

    def _append_log(self, message):
        try:
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        except Exception:
            pass

    def log(self, message):
        if threading.current_thread() == threading.main_thread():
            self._append_log(message)
        else:
            self.queue_ui_callback(0, self._append_log, message)

    def initialize_file_structure(self):
        self.log("--- Checking File Structure ---")
        missing_count = 0
        for key, path in DIRS.items():
            if key in ["quotes", "hooks", "config", "history"]:
                continue
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    self.log(f"Created: {path}")
                    missing_count += 1
                except OSError as e:
                    self.log(f"Error creating {path}: {e}")

        self.create_default_json_if_missing(DIRS["quotes"], ["Sample Quote 1", "Sample Quote 2"])
        self.create_default_json_if_missing(DIRS["hooks"], ["Hook 1", "Hook 2"])
        if missing_count > 0:
            self.label_status.configure(text="Structure Created. Add Assets!", text_color="orange")
        else:
                                                          
            has_bgs = False
            for root, _, files in os.walk(DIRS["backgrounds"]):
                for f in files:
                    if f.endswith(('.mp4', '.mov')):
                        has_bgs = True
                        break
                if has_bgs: break
            
            if not has_bgs:
                self.label_status.configure(text="Missing Background Videos!", text_color="red")
                self.btn_generate.configure(state="disabled")
            else:
                self.label_status.configure(text="System Ready", text_color="#4CAF50")
                self.btn_generate.configure(state="normal")
                self.combo_font.configure(values=self.get_font_list())

    def create_default_json_if_missing(self, path, default_content):
        if not os.path.exists(path):
            try:
                if isinstance(default_content, list):
                    content_to_save = {"Love": default_content}
                else:
                    content_to_save = default_content
                
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(content_to_save, f, ensure_ascii=False, indent=4)
                self.log(f"Created: {path}")
            except Exception as e:
                self.log(f"Error creating {path}: {e}")

    def load_available_assets(self):
                                                        
        bg_assets = {}
                                    
        if os.path.exists(DIRS["backgrounds"]):
                                                      
            subdirs = [d for d in os.listdir(DIRS["backgrounds"]) if os.path.isdir(os.path.join(DIRS["backgrounds"], d))]
            if subdirs:
                for d in subdirs:
                    path = os.path.join(DIRS["backgrounds"], d)
                    files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.mp4', '.mov'))]
                    if files:
                        bg_assets[d] = files
            
                                               
            root_files = [os.path.join(DIRS["backgrounds"], f) for f in os.listdir(DIRS["backgrounds"]) if os.path.isfile(os.path.join(DIRS["backgrounds"], f)) and f.lower().endswith(('.mp4', '.mov'))]
            if root_files:
                if "Love" in bg_assets:
                    bg_assets["Love"].extend(root_files)
                else:
                    bg_assets["Love"] = root_files
        else:
                                     
            bg_assets["Love"] = []

                    
        music_assets = {}
        if os.path.exists(DIRS["music"]):
            subdirs = [d for d in os.listdir(DIRS["music"]) if os.path.isdir(os.path.join(DIRS["music"], d))]
            if subdirs:
                for d in subdirs:
                    path = os.path.join(DIRS["music"], d)
                    files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.mp3', '.wav'))]
                    if files:
                        music_assets[d] = files
            
            root_files = [os.path.join(DIRS["music"], f) for f in os.listdir(DIRS["music"]) if os.path.isfile(os.path.join(DIRS["music"], f)) and f.lower().endswith(('.mp3', '.wav'))]
            if root_files:
                if "Love" in music_assets:
                    music_assets["Love"].extend(root_files)
                else:
                    music_assets["Love"] = root_files
        else:
             music_assets["Love"] = []

        try:
            with open(DIRS["quotes"], "r", encoding="utf-8") as f:
                quotes = json.load(f)
        except:
            quotes = {"Love": ["No quotes found"]}

        try:
            with open(DIRS["hooks"], "r", encoding="utf-8") as f:
                hooks = json.load(f)
        except:
            hooks = {"Love": ["Hook Text"]}

        sanitized_quotes = {}
        if isinstance(quotes, list):
            sanitized_quotes["default"] = [self.sanitize_text(x).replace("\n", " ") for x in quotes if isinstance(x, str)]
        else:
            for k, lst in quotes.items():
                sanitized_quotes[k] = [self.sanitize_text(x).replace("\n", " ") for x in lst if isinstance(x, str)]
                
        sanitized_hooks = {}
        if isinstance(hooks, list):
             sanitized_hooks["default"] = [self.sanitize_text(x).replace("\n", " ") for x in hooks if isinstance(x, str)]
        else:
            for k, lst in hooks.items():
                sanitized_hooks[k] = [self.sanitize_text(x).replace("\n", " ") for x in lst if isinstance(x, str)]
        return bg_assets, music_assets, sanitized_quotes, sanitized_hooks

    def select_random_quote_and_hook(self, quotes_data, hooks_data, exclude_quotes=None, target_theme=None):
        if exclude_quotes is None:
            exclude_quotes = set()

                                                              
        q_keys = set(k for k in quotes_data.keys() if k != "default" and quotes_data[k])
        h_keys = set(k for k in hooks_data.keys() if k != "default" and hooks_data[k])
        
                                        
        common_themes = list(q_keys.intersection(h_keys))
        
        theme = "Love"                   
        
        if target_theme and target_theme in quotes_data and target_theme != "All / Random":
            theme = target_theme
        elif common_themes:
                                                                    
            theme = random.choice(common_themes)
        elif q_keys:
                                                            
            theme = random.choice(list(q_keys))

                      
        source_quotes = quotes_data.get(theme, [])
        if not source_quotes:
            if "default" in quotes_data:
                source_quotes = quotes_data["default"]
            else:
                all_quotes = []
                for k in quotes_data:
                    if isinstance(quotes_data[k], list): all_quotes.extend(quotes_data[k])
                source_quotes = all_quotes

        available = [q for q in source_quotes if q not in exclude_quotes]
        if not available:
                                                                    
            available = source_quotes
            
                                                            
            if not available:
                all_quotes = []
                for k in quotes_data:
                    if isinstance(quotes_data[k], list): all_quotes.extend(quotes_data[k])
                available = [q for q in all_quotes if q not in exclude_quotes]
                if not available: available = all_quotes

        if available:
            quote = self.sanitize_text(random.choice(available)).replace("\n", " ")
        else:
            quote = "Quote text"

                                             
        h_source = hooks_data.get(theme, [])
        
                                               
        if not h_source:
             if "default" in hooks_data:
                h_source = hooks_data["default"]
             else:
                                                                                                    
                                                                                           
                 all_hooks = []
                 for k in hooks_data: 
                     if isinstance(hooks_data[k], list): all_hooks.extend(hooks_data[k])
                 h_source = all_hooks

        if not h_source:
            h_source = ["Watch this"]

        hook = self.sanitize_text(random.choice(h_source)).replace("\n", " ")
        return quote, hook, theme

    def calculate_image_brightness(self, image):
        grayscale = image.convert("L")
        stat = ImageStat.Stat(grayscale)
        return stat.mean[0]

                                                                                    
                               
                                                                                    
                                                                                
                                                          
                                                                                    
    def generate_preview_image_with_text(self, bg_image, text, hook_text, channel_name, font_name):
        w, h = bg_image.size
        bg_array = np.array(bg_image)
        txt_layer = self.generate_text_overlay_image((w, h), text, hook_text, channel_name, font_name, bg_array)
        bg_image = bg_image.convert("RGBA")
        return Image.alpha_composite(bg_image, txt_layer)

    def generate_preview(self, refresh_assets=True):
        if not MOVIEPY_AVAILABLE: return
        self.save_settings()
        
        if refresh_assets or not hasattr(self, 'preview_cache'):
            bg_assets, _, quotes, hooks = self.load_available_assets()
            
            all_bgs = []
            for k in bg_assets: all_bgs.extend(bg_assets[k])

            if not all_bgs:
                self.log("No backgrounds for preview.")
                return

            try:
                target_theme = self.combo_theme.get()
            except:
                target_theme = "All / Random"

            quote, hook, theme = self.select_random_quote_and_hook(quotes, hooks, target_theme=target_theme)
            
                                      
            if theme not in bg_assets or not bg_assets[theme]:
                messagebox.showwarning("Missing Assets", f"Theme '{theme}' is missing background videos.\nPlease download assets first.")
                self.log(f"Preview Error: Missing background videos for theme '{theme}'.")
                return
            
            candidates = list(bg_assets[theme])
            bg_path = None
            for _ in range(min(5, len(candidates))):
                temp = random.choice(candidates)
                is_ok, reason = self.verify_video_integrity(temp)
                if is_ok:
                    bg_path = temp
                    break
                else:
                    self.log(f"Preview: Skipping BG {os.path.basename(temp)} ({reason})")
                    try: candidates.remove(temp)
                    except: pass
            
            if not bg_path:
                self.log("Preview: No valid background found for preview.")
                return

            try:
                try:
                     with open(bg_path, 'rb') as f: f.read(100)
                except:
                     pass

                clip = VideoFileClip(bg_path)
                t = random.uniform(0, max(0.1, clip.duration))
                frame = clip.get_frame(t)
                clip.close()
                
                pil_img = Image.fromarray(frame)
                
                w, h = pil_img.size
                target_ratio = 9/16
                if w/h > target_ratio:
                    new_w = h * target_ratio
                    left = (w - new_w)/2
                    pil_img = pil_img.crop((left, 0, left + new_w, h))
                
                pil_img = pil_img.resize((1080, 1920), Image.Resampling.LANCZOS)
                
                self.preview_cache = {
                    "base_image": pil_img,
                    "quote": quote,
                    "hook": hook
                }
                
                self.last_generated_content = {
                    "quote": quote,
                    "hook": hook,
                    "file": "Preview Mode"
                }
                
            except Exception as e:
                self.log(f"Preview Asset Error: {e}")
                return

        if not hasattr(self, 'preview_cache'): return
        
        try:
            pil_img = self.preview_cache["base_image"].copy()
            filter_type = self.combo_filter.get()
            
            if self.var_mood_random.get():
                moods = ["None", "Darken (Cinematic)", "Black & White", "Sepia", "Vignette", "Warm Tone", "Cool Tone", "Soft Blur", "High Contrast"]
                if refresh_assets:
                    self._current_random_filter = random.choice(moods)
                
                if hasattr(self, '_current_random_filter'):
                    filter_type = self._current_random_filter
                else:
                    filter_type = random.choice(moods)
                    self._current_random_filter = filter_type
                self.log(f"Previewing Random Filter: {filter_type}")

            if filter_type == "Darken (Cinematic)":
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(0.6)
            elif filter_type == "Black & White":
                pil_img = pil_img.convert("L").convert("RGBA")
            elif filter_type == "Sepia":
                 matrix = [
                    [0.393, 0.769, 0.189], 
                    [0.349, 0.686, 0.168], 
                    [0.272, 0.534, 0.131]
                 ]
                 img_array = np.array(pil_img.convert("RGB"))
                 sepia_img = img_array.dot(np.array(matrix).T)
                 sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
                 pil_img = Image.fromarray(sepia_img).convert("RGBA")
            elif filter_type == "Warm Tone":
                 overlay = Image.new("RGBA", pil_img.size, (255, 147, 41, 50))
                 pil_img = Image.alpha_composite(pil_img.convert("RGBA"), overlay)
            elif filter_type == "Cool Tone":
                 overlay = Image.new("RGBA", pil_img.size, (0, 70, 255, 50))
                 pil_img = Image.alpha_composite(pil_img.convert("RGBA"), overlay)
            elif filter_type == "High Contrast":
                 enhancer = ImageEnhance.Contrast(pil_img)
                 pil_img = enhancer.enhance(1.5)
            elif filter_type == "Soft Blur":
                 w, h = pil_img.size
                 pil_img = pil_img.resize((w//4, h//4), Image.Resampling.BILINEAR)
                 pil_img = pil_img.resize((w, h), Image.Resampling.BILINEAR)
            elif filter_type == "Vignette":
                 pass
                 enhancer = ImageEnhance.Brightness(pil_img)
                 pil_img = enhancer.enhance(0.8)

            quote = self.preview_cache["quote"]
            hook = self.preview_cache["hook"]
            try:
                if hasattr(self, 'var_show_hook') and not self.var_show_hook.get():
                    hook = ""
            except:
                pass
            
            tiktok_name = self.entry_tiktok.get() or ""
            ig_name = self.entry_ig.get() or ""
            if tiktok_name and ig_name:
                channel = f"{tiktok_name}|||{ig_name}"
            else:
                channel = tiktok_name or ig_name
            
            if self.var_random_font.get():
                font_list = self.get_font_list()
                if font_list:
                    font_name = random.choice(font_list)
                    self.combo_font.set(font_name)
                else:
                    font_name = self.combo_font.get()
            else:
                font_name = self.combo_font.get()
            
            final_img = self.generate_preview_image_with_text(pil_img, quote, hook, channel, font_name)
            box_h = self.preview_box.winfo_height()
            box_w = self.preview_box.winfo_width()
            if box_h < 100: box_h = 500
            if box_w < 100: box_w = 300
            pad = 10
            max_h = box_h - pad
            max_w = box_w - pad
            target_ratio = 9/16
            
            if max_w / max_h > target_ratio:
                display_h = max_h
                display_w = int(display_h * target_ratio)
            else:
                display_w = max_w
                display_h = int(display_w / target_ratio)
                
            if display_w < 1: display_w = 1
            if display_h < 1: display_h = 1
            preview_img = final_img.resize((int(display_w), int(display_h)), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=preview_img, dark_image=preview_img, size=(display_w, display_h))
            self.preview_image_ref = ctk_img
            self.lbl_preview_img.configure(image=ctk_img, text="")
            
            if refresh_assets:
                self.log("Preview generated.")
                
        except Exception as e:
            self.log(f"Preview Render Error: {e}")


    def generate_ai_content(self, theme, ctype, api_key):
        try:
            client = Groq(api_key=api_key)
            if ctype == "Quotes":
                prompt = f"Generate 10 short, emotional, and viral quotes about '{theme}' in Thai language. Return only the quotes, one per line. No numbers, no english translations."
            else:
                prompt = f"Generate 10 short, viral hooks (first sentences for videos) about '{theme}' in Thai language. Return only the hooks, one per line. No numbers, no english translations."
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
            )
            
            content = chat_completion.choices[0].message.content
            lines = [line.strip().strip('"').strip("'") for line in content.split('\n') if line.strip()]
            return lines
        except Exception as e:
            self.log(f"AI Error: {e}")
            return []

    def generate_tts(self, text, filename, voice):
        async def _run_edge_tts():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filename)
            
        try:
            asyncio.run(_run_edge_tts())
            return True
        except Exception as e:
            pass
            return False
                                                                   
    def start_generation(self):
        if self.is_generating:
            self.is_generating = False
            self.btn_generate.configure(text="STOPPING...", fg_color="#F44336")
            self.log("Stopping generation... (Wait for current file)")
            return

        self.save_settings()
        try:
            count = int(self.entry_count.get())
        except:
            count = 1
                         
        try:
            target_theme = self.combo_theme.get()
        except:
            target_theme = "All / Random"

                                                          
        if target_theme != "All / Random":
            bg_path = os.path.join(DIRS["backgrounds"], target_theme)
            music_path = os.path.join(DIRS["music"], target_theme)
            
            has_bg = False
            if os.path.exists(bg_path):
                has_bg = any(f.lower().endswith(('.mp4', '.mov')) for f in os.listdir(bg_path))
            
            has_music = False
            if os.path.exists(music_path):
                has_music = any(f.lower().endswith(('.mp3', '.wav')) for f in os.listdir(music_path))
            
            if not has_bg or not has_music:
                missing = []
                if not has_bg: missing.append("Background Videos")
                if not has_music: missing.append("Music")
                
                messagebox.showwarning("Missing Assets", f"Theme '{target_theme}' is missing: {', '.join(missing)}.\nPlease download assets first.")
                return

        if not MOVIEPY_AVAILABLE:
            messagebox.showerror("Missing Dependency", "MoviePy is required to generate videos.\nInstall with:\n    pip install moviepy\nThen restart the app.")
            return

        self.is_generating = True
        self.generated_current = 0
        self.generated_total = count
        self.lbl_generated_count.configure(text=f"Generated: {self.generated_current} / {self.generated_total}")
        self.btn_generate.configure(state="normal", text="STOP (Click to Cancel)", fg_color="#D32F2F")
        self.progress.set(0)

        thread = threading.Thread(target=self.run_generation, args=(count, target_theme))
        thread.start()

    def apply_video_effects(self, clip, filter_name, duration):
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
        elif filter_name == "Soft Blur":
            w, h = clip.size
            clip = _mp_resize(_mp_resize(clip, 0.25), (w, h))
        elif filter_name == "Vignette":
            def vignette_fl(im):
                im = im * 0.8
                im = (im - 128) * 1.1 + 128
                return np.clip(im, 0, 255).astype('uint8')
            clip = _mp_transform_frames(clip, vignette_fl)
            
        if self.var_dynamic_zoom.get():
            clip = _mp_resize(clip, lambda t: 1 + (0.05 * t / duration))
            clip = _mp_set_position(clip, "center")

        if self.var_fade_in.get():
            clip = _mp_fade_in(clip, 1.0)
        if self.var_fade_out.get():
            clip = _mp_fade_out(clip, 1.0)
            
        return clip

    def verify_video_integrity(self, file_path):
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy is not installed"

        if not os.path.exists(file_path):
            return False, "File not found"
        
        if os.path.getsize(file_path) < 1024:
             return False, "File too small (likely header only)"
         
        try:
            try:
                from moviepy.editor import VideoFileClip
            except ImportError:
                from moviepy import VideoFileClip
            temp_clip = VideoFileClip(file_path)
            dur = temp_clip.duration
            temp_clip.close()
            
            if not dur or dur <= 0:
                return False, "Invalid duration"
                
        except Exception as e:
            return False, f"Corrupt file: {str(e)}"
            
        return True, "OK"

    def run_generation(self, count, target_theme=None):
        if not MOVIEPY_AVAILABLE:
            self.log("❌ Error: MoviePy is not installed. Install with 'pip install moviepy'.")
            self.is_generating = False
            self.btn_generate.configure(text="GENERATE", fg_color=self.app.color_accent if hasattr(self, 'app') else "#3B8ED0")
            return

        bg_assets, music_assets, quotes, hooks = self.load_available_assets()

        all_bgs = []
        for k in bg_assets:
            all_bgs.extend(bg_assets[k])

        used_quotes = set()
        if os.path.exists(DIRS.get("history", "config/history.json")):
            try:
                with open(DIRS.get("history", "config/history.json"), "r", encoding="utf-8") as f:
                    hist_data = json.load(f)
                    used_quotes = set(hist_data.get("used_quotes", []))
            except:
                pass

        tiktok_name = self.entry_tiktok.get() or ""
        ig_name = self.entry_ig.get() or ""
        if tiktok_name and ig_name:
            channel_name = f"{tiktok_name}|||{ig_name}"
        else:
            channel_name = tiktok_name or ig_name
        
        duration = _parse_duration_seconds(self.combo_duration.get(), default=15)
        
        base_font_name = self.combo_font.get()
        use_random_font = self.var_random_font.get()
        font_list = self.get_font_list()

        volume = self.slider_volume.get()
        logo_type = "Text"
        logo_path = ""
        fade_audio_in = self.var_fade_in.get()
        fade_audio_out = self.var_fade_out.get()
        show_prog_bar = self.var_prog_bar.get()
        video_filter = self.combo_filter.get()
        
        tts_enabled = self.var_tts.get()
        tts_voice = self.settings.get("tts_voice", "th-TH-NiwatNeural")

        if not all_bgs:
            self.is_generating = False
            self.btn_generate.configure(text="GENERATE", fg_color=self.app.color_accent if hasattr(self, 'app') else "#3B8ED0")
            return

        self.log(f"Starting batch of {count}...")

        for i in range(count):
            if not self.is_generating:
                break

            try:
                self.log(f"Processing {i+1}/{count}...")

                if use_random_font and font_list:
                    font_name = random.choice(font_list)
                    self.after(0, lambda f=font_name: self.combo_font.set(f))
                else:
                    font_name = base_font_name
                                
                current_target_theme = target_theme if target_theme else "All / Random"
                quote, hook, theme = self.select_random_quote_and_hook(quotes, hooks, exclude_quotes=used_quotes, target_theme=current_target_theme)
                bg_path = None             
                potential_bgs = []
                if theme in bg_assets and bg_assets[theme]:
                    potential_bgs = bg_assets[theme]
                else:
                    self.log(f"❌ Error: No background videos found for theme '{theme}'. Please download assets first.")
                    self.is_generating = False
                    self.btn_generate.configure(text="GENERATE", fg_color=self.app.color_accent if hasattr(self, 'app') else "#3B8ED0")                                    
                    break

                for _ in range(5):
                    if not potential_bgs: break
                    temp_bg = random.choice(potential_bgs)
                    is_valid_bg, reason_bg = self.verify_video_integrity(temp_bg)
                    if is_valid_bg:
                        bg_path = temp_bg
                        break
                    else:
                        self.log(f"⚠ Skipping corrupt BG: {os.path.basename(temp_bg)} ({reason_bg})")
                
                if not bg_path:
                    self.log(f"❌ Error: No valid background videos found for theme '{theme}'.")
                    self.is_generating = False
                    break

                                             
                music_path = None
                
                if theme in music_assets and music_assets[theme]:
                    music_path = random.choice(music_assets[theme])
                else:
                     self.log(f"❌ Error: No music found for theme '{theme}'. Please download assets first.")
                     self.is_generating = False
                     break
                
                if self.var_mood_random.get():
                    moods = ["None", "Darken (Cinematic)", "Black & White", "Sepia", "Vignette", "Warm Tone", "Cool Tone", "Soft Blur", "High Contrast"]
                    video_filter = random.choice(moods)

                self.last_generated_content = {
                    "quote": quote,
                    "hook": hook,
                    "file": f"Batch {i+1}"
                }

                if quote not in used_quotes:
                    used_quotes.add(quote)
                    try:
                        with open(DIRS.get("history", "config/history.json"), "w", encoding="utf-8") as f:
                            json.dump({"used_quotes": list(used_quotes)}, f, ensure_ascii=False, indent=4)
                    except:
                        pass
                
                if not self.is_generating: break

                clip = VideoFileClip(bg_path)

                if clip.duration < duration:
                    if self.var_stretch.get():
                        factor = clip.duration / duration
                        clip = _mp_speedx(clip, factor)
                    else:
                        loop_count = int(duration / clip.duration) + 1
                        clip = _mp_subclip(_mp_loop_clip(clip, n=loop_count), 0, duration)
                else:
                    start = random.uniform(0, clip.duration - duration)
                    clip = _mp_subclip(clip, start, start + duration)

                w, h = clip.size
                target_ratio = 9/16
                if w/h > target_ratio:
                    new_w = h * target_ratio
                    clip = _mp_crop(clip, x1=w/2 - new_w/2, x2=w/2 + new_w/2)

                clip = _mp_resize(clip, height=1920)
                if clip.w != 1080:
                    clip = _mp_resize(clip, width=1080)

                clip = self.apply_video_effects(clip, video_filter, duration)
                
                if not self.is_generating: 
                    clip.close()
                    break

                audio_clips = []
                tts_file = None
                if tts_enabled:
                    clean_text = quote.replace('"', '').replace("'", "").strip()
                    tts_filename = f"tts_{datetime.now().strftime('%H%M%S%f')}.mp3"
                    tts_file = os.path.join(DIRS["output"], tts_filename)
                    
                    self.log("Generating TTS Audio...")
                    if self.generate_tts(clean_text, tts_file, tts_voice):
                        try:
                            tts_audio = AudioFileClip(tts_file)
                            tts_audio = _mp_set_start(tts_audio, 0.5)
                            audio_clips.append(tts_audio)
                        except Exception as e:
                            self.log(f"Error loading TTS audio: {e}")
                    else:
                        self.log("Failed to generate TTS.")

                if music_path:
                    music_audio = AudioFileClip(music_path)
                    if music_audio.duration < duration:
                        music_audio = _mp_loop_audio(music_audio, duration)
                    else:
                        start = random.uniform(0, music_audio.duration - duration)
                        music_audio = _mp_subclip(music_audio, start, start + duration)

                    music_audio = _mp_volumex(music_audio, volume)
                    if tts_file and len(audio_clips) > 0:
                         music_audio = _mp_volumex(music_audio, 0.3)

                    if fade_audio_in:
                        music_audio = _mp_audio_fade_in(music_audio, 2)
                    if fade_audio_out:
                        music_audio = _mp_audio_fade_out(music_audio, 2)
                    
                    audio_clips.append(music_audio)

                if audio_clips:
                    comp_audio = CompositeAudioClip(audio_clips)
                    clip = _mp_set_audio(clip, comp_audio)

                ref_frame = clip.get_frame(0)
                logo_arg = logo_path if logo_type == "Image" and os.path.exists(logo_path) else channel_name
                hook_display = hook
                try:
                    if hasattr(self, 'var_show_hook') and not self.var_show_hook.get():
                        hook_display = ""
                except:
                    hook_display = hook
                txt_layer = self.generate_text_overlay_image(clip.size, quote, hook_display, logo_arg, font_name, ref_frame, is_image_logo=(logo_type=="Image"))
                txt_clip_overlay = _mp_set_duration(ImageClip(np.array(txt_layer)), duration)
                if self.var_fade_in.get():
                    txt_clip_overlay = _mp_fade_in(txt_clip_overlay, 1.0)
                if self.var_fade_out.get():
                    txt_clip_overlay = _mp_fade_out(txt_clip_overlay, 1.0)

                layers = [clip, txt_clip_overlay]
                if show_prog_bar:
                    prog_bar = _mp_set_duration(ColorClip(size=(1080, 20), color=(233, 30, 99)), duration)
                    prog_bar = _mp_set_position(prog_bar, lambda t: (int(-1080 + (t/duration)*1080), 1900))
                    layers.append(prog_bar)

                final_clip = _mp_set_duration(CompositeVideoClip(layers), duration)
                clean_text = hook_display if (hook_display and len(hook_display) > 3) else quote
                invalid_chars = '<>:"/\\|?*'
                clean_text = "".join([c for c in clean_text if c not in invalid_chars]).strip()
                clean_text = clean_text.replace(" ", "_").replace("\n", "")[:50]
                if not clean_text: clean_text = "love_quote"
                filename = f"{clean_text}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"                   
                output_dir = os.path.join(DIRS["output"], theme)
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except:
                    output_dir = DIRS["output"]

                out_path = os.path.join(output_dir, filename)
                self.current_generating_file = out_path
                try:
                    preview_frame = final_clip.get_frame(1.0)
                    preview_img = Image.fromarray(preview_frame)
                    w_p, h_p = preview_img.size
                    scale_p = 480 / h_p
                    new_w_p = int(w_p * scale_p)
                    preview_img_resized = preview_img.resize((new_w_p, 480), Image.Resampling.NEAREST)
                    
                    ctk_preview = ctk.CTkImage(light_image=preview_img_resized, dark_image=preview_img_resized, size=(new_w_p, 480))
                    
                    def update_ui_safe():
                        if not self.is_generating: return
                        try:
                            try:
                                self.lbl_preview_img.configure(image=ctk_preview, text="")
                                self.label_status.configure(text=f"Generating: {filename} ({duration}s)")
                            except: pass
                        
                            try:
                                if hasattr(self, 'video_player') and self.video_player.winfo_exists():
                                    self.video_player.update_image(ctk_preview)
                                    self.video_player.label.configure(text=f"Generating: {filename}\nSize: 1080x1920 | Dur: {duration}s")
                            except: pass
                        except: pass

                    self.after(0, update_ui_safe)
                except Exception as e:
                    pass

                if not self.is_generating:
                    self.current_generating_file = None
                    break

                _mp_write_videofile(final_clip, out_path, codec="libx264", audio_codec="aac", fps=30, verbose=False, logger=None)
                if not self.is_generating:
                    if os.path.exists(out_path):
                        try:
                            final_clip.close()
                            os.remove(out_path)
                            self.log(f"Cleaned up incomplete file: {filename}")
                        except: pass
                    self.current_generating_file = None
                    break

                is_valid, reason = self.verify_video_integrity(out_path)
                if not is_valid:
                    self.log(f"Integrity Check Failed: {filename} ({reason})")
                    self.log(f"Auto-deleting corrupt file...")
                    try: 
                        final_clip.close()
                        if os.path.exists(out_path): os.remove(out_path)
                    except: pass
                    continue

                meta_path = out_path.replace(".mp4", ".json")
                meta_data = {
                    "file": filename,
                    "theme": theme,
                    "quote": quote,
                    "hook": hook,
                    "bg_file": os.path.basename(bg_path),
                    "music_file": os.path.basename(music_path) if music_path else None,
                    "font": font_name,
                    "tts": tts_enabled,
                    "created_at": datetime.now().isoformat()
                }
        
                                                                    
                try:
                    theme_meta_path = os.path.join(output_dir, "metadata.json")
                    
                                                      
                    existing_data = {}
                    if os.path.exists(theme_meta_path):
                        try:
                            with open(theme_meta_path, "r", encoding="utf-8") as f:
                                existing_data = json.load(f)
                        except:
                            existing_data = {}
                    
                                                 
                    existing_data[filename] = meta_data
                    
                    with open(theme_meta_path, "w", encoding="utf-8") as f:
                        json.dump(existing_data, f, ensure_ascii=False, indent=4)
                        
                except Exception as e:
                    self.log(f"⚠ Failed to save metadata: {e}")

                self.append_to_history(meta_data)
                clip.close()
                if music_path:
                    try: music_audio.close() 
                    except: pass
                if tts_file:
                    try: tts_audio.close()
                    except: pass
                    if os.path.exists(tts_file):
                        try: os.remove(tts_file)
                        except: pass

                self.progress.set((i+1)/count)
                self.generated_current = i + 1
                self.after(0, lambda: self.lbl_generated_count.configure(text=f"Generated: {self.generated_current} / {self.generated_total}"))
                self.log(f"Finished: {filename}")

            except Exception as e:
                self.log(f"Error {i+1}: {e}")
            finally:
                try: clip.close() 
                except: pass
                try: final_clip.close() 
                except: pass

        if not self.is_generating:
             self.log("Job Stopped by User.")
        else:
             self.log("Job Done!")
        
        self.is_generating = False
        self.current_generating_file = None
        self.btn_generate.configure(state="normal", text="GENERATE", fg_color=self.color_accent)

        if self.var_shutdown.get() and self.generated_current == count:
            self.log("Auto-Shutdown in 60s... (Close window to cancel)")

    def smart_balanced_wrap(self, draw, font, text, max_width, max_lines=3):
        text = self.sanitize_text(text)
        if not text:
            return []
            
        try:
            from pythainlp.tokenize import word_tokenize
            raw_tokens = word_tokenize(text, keep_whitespace=True)
        except ImportError:
            parts = text.split(' ')
            raw_tokens = []
            for i, p in enumerate(parts):
                if p: raw_tokens.append(p)
                if i < len(parts) - 1:
                    raw_tokens.append(" ")

        tokens = []
        for w in raw_tokens:
            if not w: continue
            try:
                w_width = draw.textbbox((0,0), w, font=font)[2] - draw.textbbox((0,0), w, font=font)[0]
            except:
                w_width = 0
                
            if w_width > max_width:
                 tokens.extend(self.thai_clusters(w))
            else:
                 tokens.append(w)
        
        if not tokens: return []
        best_layout = None
        best_score = float('inf')
        
        n_tokens = len(tokens)
        def score_layout(lines_indices):
            lines_widths = []
            lines_str = []
            
            for i in range(len(lines_indices)):
                start = lines_indices[i]
                end = lines_indices[i+1] if i+1 < len(lines_indices) else n_tokens
                line_toks = tokens[start:end]
                line_s = "".join(line_toks).strip()
                if not line_s:
                    lines_widths.append(0)
                    lines_str.append("")
                    continue
                
                try:
                    bbox = draw.textbbox((0,0), line_s, font=font)
                    w = bbox[2] - bbox[0]
                except:
                    w = 0
                
                if w > max_width: return float('inf'), []
                lines_widths.append(w)
                lines_str.append(line_s)

            lines_widths = [x for x in lines_widths if x > 0]
            if not lines_widths: return float('inf'), []
            avg = sum(lines_widths) / len(lines_widths)
            variance = sum((x - avg) ** 2 for x in lines_widths)
            if len(lines_widths) > 1:
                if lines_widths[-1] < avg * 0.6:
                    variance += 1000000
                    
            return variance, lines_str
        
        s, l = score_layout([0])
        if s < float('inf'):
            best_layout = l
            best_score = s

        if max_lines >= 2 and n_tokens > 1:
            for i in range(1, n_tokens):
                s, l = score_layout([0, i])
                if s < best_score:
                    best_score = s
                    best_layout = l

        if max_lines >= 3 and n_tokens > 2:
            for i in range(1, n_tokens-1):
                for j in range(i+1, n_tokens):
                    s, l = score_layout([0, i, j])
                    if s < best_score:
                        best_score = s
                        best_layout = l
                        
        return best_layout if best_layout else [text]

    def sanitize_text(self, t):
        if not t:
            return ""
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        invisibles = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2060"]
        for ch in invisibles:
            t = t.replace(ch, "")
        for ch in ['“','”','‘','’','"']:
            t = t.replace(ch, "")
        t = unicodedata.normalize("NFC", t)
        t = " ".join(t.split())
        return "\n".join([line.strip() for line in t.split("\n")])
    
    def thai_clusters(self, text):
        if not text:
            return []
        leading = set(['เ','แ','โ','ใ','ไ'])
        def is_mark(ch):
            return unicodedata.category(ch) == 'Mn' or ch in ['ั','ิ','ี','ึ','ื','ุ','ู','่','้','๊','๋','็','์']
        res = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch.isspace():
                res.append(ch)
                i += 1
                continue
            if ch in leading and i+1 < n:
                base = text[i+1]
                cluster = ch + base
                j = i + 2
                while j < n and is_mark(text[j]):
                    cluster += text[j]
                    j += 1
                res.append(cluster)
                i = j
            else:
                cluster = ch
                j = i + 1
                while j < n and is_mark(text[j]):
                    cluster += text[j]
                    j += 1
                res.append(cluster)
                i = j
        return res
    
    def join_clusters(self, clusters):
        return "".join(clusters)

                                                                                    
                                           
                                                                                    
                                                                               
                                                                               
                                                                                    
    def thai_wrap_px(self, draw, font, text, max_px):
        if not text:
            return []
        no_start = ['ั', 'ิ', 'ี', 'ึ', 'ื', '็', '์', 'ุ', 'ู', '่', '้', '๊', '๋', 'ำ']
        def width(s):
            if not s:
                return 0
            b = draw.textbbox((0,0), s, font=font, anchor="ls")
            return b[2] - b[0]
        res = []
        curr_clusters = []
        for token in self.thai_clusters(text):
            cand = self.join_clusters(curr_clusters + [token])
            if width(cand) <= max_px:
                curr_clusters.append(token)
                continue
            if self.join_clusters(curr_clusters).strip():
                res.append(self.join_clusters(curr_clusters).strip())
                curr_clusters = []
            if width(token) <= max_px:
                curr_clusters.append(token)
                continue
            buf = []
            for ch in self.thai_clusters(token):
                test = self.join_clusters(buf + [ch])
                if width(test) <= max_px:
                    buf.append(ch)
                else:
                    if (ch and (ch[0] in no_start or unicodedata.category(ch[0]) == 'Mn')) and len(buf) > 0:
                        buf.append(ch)
                    else:
                        if self.join_clusters(buf).strip():
                            res.append(self.join_clusters(buf).strip())
                            buf = [ch]
                        else:
                            buf = [ch]
            curr_clusters = buf
        if self.join_clusters(curr_clusters).strip():
            res.append(self.join_clusters(curr_clusters).strip())
        return [l for l in res if l]

    def natural_wrap_thai(self, draw, font, text, max_px, max_lines=3):
        text = self.sanitize_text(text)
        if not text:
            return []
        if " " not in text:
            return self.thai_wrap_px(draw, font, text, max_px)
        connectors = set(["แต่","เพราะ","เพราะว่า","และ","เมื่อ","เพื่อ","ถ้า","หาก","แล้ว","จน","ก็","ในวันที่","ในวัน","เพียง","แม้","ทว่า"])
        tokens = text.split(" ")
        res = []
        curr = ""
        def w(s):
            b = draw.textbbox((0,0), s, font=font, anchor="ls")
            return b[2]-b[0]
        for t in tokens:
            cand = (curr + " " + t).strip()
            if t in connectors and curr:
                res.append(curr.strip())
                curr = t
                continue
            if w(cand) <= max_px:
                curr = cand
            else:
                if curr:
                    res.append(curr.strip())
                    curr = t
                else:
                    lines = self.thai_wrap_px(draw, font, t, max_px)
                    res.extend(lines)
                    curr = ""
            if len(res) >= max_lines:
                break
        if curr and len(res) < max_lines:
            res.append(curr.strip())
        return [l for l in res if l][:max_lines]

    def fix_thai_vowel_overlap(self, text):
        return text

    def draw_thai_text(self, draw, xy, text, font, fill, anchor=None):
        x, y = xy
        if not re.search(r'[\u0E00-\u0E7F]', text):
            draw.text(xy, text, font=font, fill=fill, anchor=anchor)
            return
        
        if anchor:
            bbox = draw.textbbox(xy, text, font=font, anchor=anchor)
            x, y = bbox[0], bbox[1]
        UPPER_VOWELS = set(['\u0E31', '\u0E34', '\u0E35', '\u0E36', '\u0E37', '\u0E4D', '\u0E47'])
        TONES = set(['\u0E48', '\u0E49', '\u0E4A', '\u0E4B', '\u0E4C'])
        
        cursor_x = x
        i = 0
        length = len(text)
        
        while i < length:
            char = text[i]
            is_upper_vowel = char in UPPER_VOWELS
            next_char = text[i+1] if i + 1 < length else None
            
            if is_upper_vowel and next_char in TONES:
                draw.text((cursor_x, y), char, font=font, fill=fill)
                w_vowel = font.getlength(char)
                lift = font.size * 0.25
                draw.text((cursor_x + w_vowel, y - lift), next_char, font=font, fill=fill)
                cursor_x += w_vowel + font.getlength(next_char)
                i += 2
            else:
                draw.text((cursor_x, y), char, font=font, fill=fill)
                cursor_x += font.getlength(char)
                i += 1

    def generate_text_overlay_image(self, size, text, hook_text, logo_arg, font_name, ref_frame_array, is_image_logo=False):
        w, h = size
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if ref_frame_array.dtype != np.uint8:
            ref_frame_array = np.clip(ref_frame_array, 0, 255).astype(np.uint8)

        ref_img = Image.fromarray(ref_frame_array).convert("L")
        center_crop = ref_img.crop((w*0.1, h*0.4, w*0.9, h*0.7))
        stat = ImageStat.Stat(center_crop)
        brightness = stat.mean[0]

        if brightness > 128:
            text_color = (0, 0, 0, 255)
            shadow_color = (255, 255, 255, 128)
            if self.var_backdrop.get():
                box_color = (255, 255, 255, 140)
            else:
                box_color = (0, 0, 0, 0)
        else:
            text_color = (255, 255, 255, 255)
            shadow_color = (0, 0, 0, 128)
            
            if self.var_backdrop.get():
                op = self.settings.get("backdrop_opacity", 0.4)
                box_color = (0, 0, 0, int(255 * op))
            else:
                box_color = (0, 0, 0, 0)

        font_path = None
        if font_name and font_name != "Default":
            font_path = os.path.join(DIRS["fonts"], font_name)

        BODY_FONT_SIZE = 78
        HOOK_FONT_SIZE = 104
        WM_FONT_SIZE = 40

        try:
            font_candidates = []
            if font_path:
                font_candidates.append(font_path)
            font_candidates.extend([
                os.path.join(DIRS["fonts"], "NotoSansThai-Regular.ttf"),
                os.path.join(DIRS["fonts"], "THSarabunNew.ttf"),
                "C:\\Windows\\Fonts\\Tahoma.ttf",
                "arial.ttf"
            ])
            font = None
            for cand in font_candidates:
                try:
                    font = ImageFont.truetype(cand, BODY_FONT_SIZE)
                    break
                except:
                    continue
            if font is None:
                font = ImageFont.load_default()

            hook_font = None
            for cand in font_candidates:
                try:
                    hook_font = ImageFont.truetype(cand, HOOK_FONT_SIZE)
                    break
                except:
                    continue
            if hook_font is None:
                hook_font = ImageFont.load_default()
            wm_font = None
            for cand in font_candidates:
                try:
                    wm_font = ImageFont.truetype(cand, WM_FONT_SIZE)
                    break
                except:
                    continue
            if wm_font is None:
                wm_font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            hook_font = ImageFont.load_default()
            wm_font = ImageFont.load_default()
            
        hook_center_x = w / 2
        show_hook = True
        try:
            show_hook = self.var_show_hook.get()
        except:
            try:
                show_hook = self.settings.get("show_hook_text", True)
            except:
                show_hook = True
        hook_center_y = h * 0.15
        pad_x = 40
        pad_y = 20
        hook_box_w = int(w * 0.82)
        hook_box_h = int(h * 0.09)
        box_x1 = hook_center_x - (hook_box_w / 2)
        box_y1 = hook_center_y - (hook_box_h / 2)
        box_x2 = hook_center_x + (hook_box_w / 2)
        box_y2 = hook_center_y + (hook_box_h / 2)
        if show_hook and hook_text and len(str(hook_text).strip()) > 0:
            draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=box_color)
            hook_text = self.sanitize_text(hook_text)
            hook_max_px = hook_box_w - (pad_x * 2)
            hook_lines = self.thai_wrap_px(draw, hook_font, hook_text, hook_max_px)
            dummy_hook = "ที่ปู่นี้จ้ะ"
            dummy_bbox = draw.textbbox((0, 0), dummy_hook, font=hook_font, anchor="ls")
            hook_line_h = dummy_bbox[3] - dummy_bbox[1]
            hook_spacing = hook_line_h * 0.6
            total_hook_h = (hook_line_h * len(hook_lines)) + (hook_spacing * max(0, len(hook_lines)-1))
            need_scale = False
            max_hook_w = 0
            for ln in hook_lines:
                lb = draw.textbbox((0,0), ln, font=hook_font, anchor="ls")
                max_hook_w = max(max_hook_w, lb[2]-lb[0])
            if max_hook_w > hook_max_px or total_hook_h > (hook_box_h - 2*pad_y):
                need_scale = True
            if need_scale:
                target_w = hook_max_px
                target_h = hook_box_h - 2*pad_y
                size = HOOK_FONT_SIZE
                while size > 20:
                    built = False
                    for cand in font_candidates:
                        try:
                            hook_font = ImageFont.truetype(cand, size)
                            built = True
                            break
                        except:
                            continue
                    if not built:
                        break
                    dummy_bbox = draw.textbbox((0, 0), dummy_hook, font=hook_font, anchor="ls")
                    hook_line_h = dummy_bbox[3] - dummy_bbox[1]
                    hook_spacing = hook_line_h * 0.6
                    hook_lines = self.thai_wrap_px(draw, hook_font, hook_text, hook_max_px)
                    max_hook_w = 0
                    for ln in hook_lines:
                        lb = draw.textbbox((0,0), ln, font=hook_font, anchor="ls")
                        max_hook_w = max(max_hook_w, lb[2]-lb[0])
                    total_hook_h = (hook_line_h * len(hook_lines)) + (hook_spacing * max(0, len(hook_lines)-1))
                    if max_hook_w <= target_w and total_hook_h <= target_h:
                        break
                    size = int(size * 0.92)
                    
            if len(hook_lines) > 2:
                hook_lines = hook_lines[:2]
            total_h = (hook_line_h * len(hook_lines)) + (hook_spacing * max(0, len(hook_lines)-1))
            start_y = hook_center_y - (total_h / 2) + (hook_line_h / 2)
            for line in hook_lines:
                line_fixed = self.fix_thai_vowel_overlap(line)
                
                if self.var_smart_shadow.get():
                    offsets = [(2,2), (-2,-2), (2,-2), (-2,2), (0,3), (0,-3), (3,0), (-3,0)]
                    for ox, oy in offsets:
                         self.draw_thai_text(draw, (hook_center_x + ox, start_y + oy), line_fixed, font=hook_font, fill=shadow_color, anchor="mm")
                else:
                    self.draw_thai_text(draw, (hook_center_x + 2, start_y + 2), line_fixed, font=hook_font, fill=shadow_color, anchor="mm")
                    
                self.draw_thai_text(draw, (hook_center_x, start_y), line_fixed, font=hook_font, fill=text_color, anchor="mm")
                start_y += hook_line_h + hook_spacing

        text = self.sanitize_text(text)
        body_pad_x = 40
        body_pad_y = 20
        body_box_w = int(w * 0.85)
        body_box_h = int(h * 0.24)
        max_line_px = body_box_w - 2*body_pad_x
        lines = self.smart_balanced_wrap(draw, font, text, max_line_px, max_lines=3)
        dummy_text = "ที่ปู่นี้จ้ะ" 
        dummy_bbox = draw.textbbox((0, 0), dummy_text, font=font, anchor="ls")
        line_height = dummy_bbox[3] - dummy_bbox[1]
        line_spacing = line_height * 0.72
        center_y = h * 0.55 if show_hook else h * 0.50
        
        allowed_w = body_box_w - 2*body_pad_x
        allowed_h = body_box_h - 2*body_pad_y
        size = BODY_FONT_SIZE
        def calc_dims(fs):
            fnt = None
            for cand in font_candidates:
                try:
                    fnt = ImageFont.truetype(cand, fs)
                    break
                except:
                    continue
            if fnt is None:
                fnt = font
            db = draw.textbbox((0, 0), dummy_text, font=fnt, anchor="ls")
            lh = db[3] - db[1]
            ls = lh * 0.72
            tw = 0
            th = (lh * len(lines)) + (ls * max(0, len(lines)-1))
            for ln in lines:
                lb = draw.textbbox((0,0), ln, font=fnt, anchor="ls")
                tw = max(tw, lb[2]-lb[0])
            return fnt, lh, ls, tw, th
        fnt, lh, ls, tw, th = calc_dims(size)
        font = fnt
        line_height = lh
        line_spacing = ls
        max_line_w = tw
        total_text_height = th
        while (tw > allowed_w or th > allowed_h) and size > 24:
            size = int(size * 0.92)
            font, line_height, line_spacing, max_line_w, total_text_height = calc_dims(size)
            lines = self.smart_balanced_wrap(draw, font, text, max_line_px, max_lines=3)
            fnt, lh, ls, tw, th = calc_dims(size)
            font = fnt
            line_height = lh
            line_spacing = ls
            total_text_height = th
        box_x1 = (w - body_box_w) / 2
        box_y1 = center_y - (body_box_h / 2)
        box_x2 = box_x1 + body_box_w
        box_y2 = center_y + (body_box_h / 2)

        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=box_color)

        text_block_top = center_y - (total_text_height / 2)
        curr_y = text_block_top + (line_height / 2)
        for ln in lines:
            ln_fixed = self.fix_thai_vowel_overlap(ln)
            
            if self.var_smart_shadow.get():
                offsets = [(2,2), (-2,-2), (2,-2), (-2,2), (0,3), (0,-3), (3,0), (-3,0)]
                for ox, oy in offsets:
                    self.draw_thai_text(draw, (w/2 + ox, curr_y + oy), ln_fixed, font=font, fill=shadow_color, anchor="mm")
            else:
                self.draw_thai_text(draw, (w/2 + 2, curr_y + 2), ln_fixed, font=font, fill=shadow_color, anchor="mm")
                
            self.draw_thai_text(draw, (w/2, curr_y), ln_fixed, font=font, fill=text_color, anchor="mm")
            curr_y += line_height + line_spacing
        wm_y = int(h*0.85)

        if is_image_logo and os.path.exists(logo_arg):
            try:
                logo = Image.open(logo_arg).convert("RGBA")
                lw, lh = logo.size
                target_lw = 200
                target_lh = int(lh * (target_lw/lw))
                logo = logo.resize((target_lw, target_lh), Image.Resampling.LANCZOS)

                logo_x = int((w - target_lw) / 2)
                img.paste(logo, (logo_x, wm_y), logo)
            except:
                bbox_wm = draw.textbbox((0,0), "Logo Error", font=wm_font)
                wm_x = (w - (bbox_wm[2]-bbox_wm[0])) / 2
                draw.text((wm_x, wm_y), "Logo Error", font=wm_font, fill=(255, 255, 255, 128))
        else:
            names = logo_arg.split("|||")
            current_y = wm_y
            for name in names:
                name = name.strip()
                if not name: continue
                bbox_wm = draw.textbbox((0,0), name, font=wm_font)
                text_w_px = bbox_wm[2] - bbox_wm[0]
                text_h_px = bbox_wm[3] - bbox_wm[1]
                max_x = int(w - text_w_px - 50)
                if max_x < 50: max_x = 50
                wm_x = random.randint(50, max_x)
                draw.text((wm_x, current_y), name, font=wm_font, fill=(255, 255, 255, 128))
                current_y += text_h_px + 10

        return img

    def load_posted_history(self):
        posted = set()
        json_log_file = os.path.join("config", "social_history.json")
        if os.path.exists(json_log_file):
            try:
                with open(json_log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if entry.get("status") == "Success":
                                posted.add((entry.get("platform"), entry.get("filename")))
            except: pass
        return posted

    def randomly_select_videos_in_queue(self):
        try:
            qty = int(self.entry_sel_qty.get())
        except:
            qty = 1

        for _, var in self.queue_vars:
            var.set(False)

        indices = list(range(len(self.queue_vars)))
        random.shuffle(indices)
        for i in indices[:qty]:
            self.queue_vars[i][1].set(True)

    def refresh_video_list(self):
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()
        self.queue_vars = []

        if not os.path.exists(DIRS["output"]):
            return

        files = []
        for root, dirs, filenames in os.walk(DIRS["output"]):
            for filename in filenames:
                if filename.lower().endswith(('.mp4', '.avi', '.mov')):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, DIRS["output"])
                    files.append(rel_path)

        files.sort(key=lambda x: os.path.getmtime(os.path.join(DIRS["output"], x)), reverse=True)
        posted_history = self.load_posted_history()
        posted_filenames = {fname for _, fname in posted_history}

                          
        filter_theme = "All"
        if hasattr(self, 'combo_queue_filter'):
            filter_theme = self.combo_queue_filter.get()

        for f in files:
            if f in posted_filenames or os.path.basename(f) in posted_filenames:
                continue

                                       
            if filter_theme != "All":
                full_path = os.path.join(DIRS["output"], f)
                json_path = os.path.splitext(full_path)[0] + ".json"
                video_theme = "Unknown"
                
                                                                                
                parts = os.path.split(f)
                if len(parts) > 1 and parts[0] != "":
                     video_theme = parts[0]

                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as jf:
                            data = json.load(jf)
                            video_theme = data.get("theme", video_theme)
                    except: pass
                
                if video_theme != filter_theme:
                    continue

            var = ctk.BooleanVar(value=False)
            display_text = f
            text_color = "#ccc"
            chk = ctk.CTkCheckBox(self.queue_scroll, text=display_text, variable=var, text_color=text_color)
            chk.pack(anchor="w", pady=2)
            self.queue_vars.append((f, var))
            
        if hasattr(self, 'lbl_queue_header'):
            self.lbl_queue_header.configure(text=f"Video Queue ({len(self.queue_vars)})")

        try:
            total_remaining = len(self.queue_vars)
            used_count = sum(1 for f in files if f in posted_filenames)
            self.lbl_queue_header.configure(text=f"Video Queue (Used: {used_count} | Remaining: {total_remaining})")
        except: pass

    def select_all_queue(self):
        for _, var in self.queue_vars:
            var.set(True)

    def log_social_activity(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}\n"
        try:
            self.soc_log_box.configure(state="normal")
            self.soc_log_box.insert("end", full_msg)
            self.soc_log_box.see("end")
            self.soc_log_box.configure(state="disabled")
        except: pass

        try:
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", full_msg)
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        except: pass

    def close_browser(self):
        if self.active_automator:
            try:
                self.active_automator.driver.quit()
                self.log_social_activity("Browser closed.")
            except:
                pass
            self.active_automator = None
        else:
            self.log_social_activity("No active browser to close.")

    def open_login_browser(self):
        if not SELENIUM_AVAILABLE:
            self.log_social_activity("Error: Selenium not installed.")
            return

        threading.Thread(target=self.run_login_browser).start()

    def run_login_browser(self):
        self.close_browser()
        self.log_social_activity("Opening Login Browser...")
        self.log_social_activity("Please Login to TikTok/Instagram/Facebook in this window.")
        self.log_social_activity("Close the window when finished.")
        self.active_automator = SocialMediaAutomator(self.log_social_activity)
        if self.active_automator.start_browser():
            self.active_automator.driver.execute_script("window.open('https://www.tiktok.com/login', '_blank');")
            self.active_automator.driver.execute_script("window.open('https://www.facebook.com/login', '_blank');")
            self.active_automator.driver.get("https://www.instagram.com/accounts/login/")
            try:
                while self.active_automator:
                    time.sleep(1)
                    if self.active_automator: _ = self.active_automator.driver.title
            except:
                self.log_social_activity("Login Browser Closed.")
                self.active_automator = None

    def execute_schedule_loop(self):
        self.log_social_activity("📅 Starting Schedule Mode...")
        self.log_social_activity("Checking for pending posts...")
        
        catchup_count = 0
        try:
            catchup_gap = float(self.entry_interval.get()) * 60
        except:
            catchup_gap = 0
        last_notified_day = None
        
        while self.post_running:
            try:
                                   
                date_str, slot = self.schedule_manager.get_next_pending_slot()
                
                if not slot:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    if last_notified_day != today_str:
                        self.log_social_activity("📣 วันนี้ลงคลิปครบตามกำหนดแล้ว รอวันถัดไป")
                        try:
                            self.after(0, lambda: messagebox.showinfo("แจ้งเตือน", "วันนี้ลงคลิปครบตามกำหนดแล้ว รอวันถัดไป"))
                        except: pass
                        if self.active_automator:
                            self.log_social_activity("✅ All scheduled posts for today are done.")
                            self.log_social_activity("Closing browser as requested...")
                            try:
                                self.active_automator.close()
                            except: pass
                            self.active_automator = None
                            self.log_social_activity("✨ Schedule execution completed according to plan.")
                        last_notified_day = today_str

                                                     
                    for _ in range(10):
                        if not self.post_running: break
                        time.sleep(1)
                    continue
                
                target_time_str = slot['time']          
                file_rel_path = slot['file']
                
                            
                now = datetime.now()
                target_time = datetime.strptime(target_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                
                wait_seconds = (target_time - now).total_seconds()
                
                if wait_seconds > 0:
                          
                    self.log_social_activity(f"⏳ Waiting for schedule: {target_time_str} ({int(wait_seconds/60)}m)...")
                    while wait_seconds > 0:
                        if not self.post_running: break
                        time.sleep(1)                     
                        wait_seconds -= 1
                        if wait_seconds % 60 == 0 and wait_seconds > 60:
                             self.log_social_activity(f"⏳ Schedule: {int(wait_seconds/60)}m remaining...")
                    
                    if not self.post_running: break
                else:
                    if catchup_count >= 1 and catchup_gap > 0:
                        self.log_social_activity(f"⏳ Catch-up gap: {int(catchup_gap)}s before next post...")
                        for _ in range(int(catchup_gap)):
                            if not self.post_running: break
                            time.sleep(1)
                
                               
                self.log_social_activity(f"⏰ Executing Schedule: {file_rel_path}")
                
                            
                full_path = os.path.join(DIRS["output"], file_rel_path)
                if not os.path.exists(full_path):
                    self.log_social_activity(f"❌ File not found: {file_rel_path}")
                    self.schedule_manager.update_slot_status(date_str, target_time_str, "failed")
                    continue

                                                      
                if not self.active_automator:
                    self.log_social_activity("Initializing Browser...")
                    self.active_automator = SocialMediaAutomator(self.log_social_activity, headless=self.var_headless.get())
                    if not self.active_automator.start_browser():
                         self.log_social_activity("Failed to start browser.")
                         self.post_running = False
                         break
                
                automator = self.active_automator
                
                                   
                platforms = []
                if self.var_tiktok.get(): platforms.append("TikTok")
                if self.var_ig.get(): platforms.append("Instagram")
                if self.var_yt.get(): platforms.append("Shorts")
                if self.var_fb.get(): platforms.append("Facebook")
                
                if not platforms:
                    self.log_social_activity("Error: No platforms selected!")
                    self.post_running = False
                    break

                if not automator.prepare_sessions(platforms):
                    self.log_social_activity("Session preparation failed.")
                    self.post_running = False
                    break

                                  
                caption = self.generate_smart_caption(os.path.basename(full_path))
                
                        
                all_success = True
                for p in platforms:
                    self.log_social_activity(f"Posting to {p}...")
                    res = "Unknown"
                    if p == "TikTok": res = automator.upload_tiktok(os.path.abspath(full_path), caption)
                    elif p == "Instagram": res = automator.upload_instagram(os.path.abspath(full_path), caption)
                    elif p == "Shorts": res = automator.upload_shorts(os.path.abspath(full_path), caption)
                    elif p == "Facebook": res = automator.upload_facebook(os.path.abspath(full_path), caption)
                    
                    if "Error" in res:
                        self.log_social_activity(f"❌ {p} Error: {res}")
                        all_success = False
                    elif "Manual" in res:
                        self.log_social_activity(f"⚠ {p}: Waiting for manual confirmation (60s)...")
                        for _ in range(60):
                            if not self.post_running: break
                            time.sleep(1)
                    else:
                        self.save_post_log_file(p, file_rel_path, "Success", "")
                        self.increment_daily_count()

                if all_success:
                    self.schedule_manager.update_slot_status(date_str, target_time_str, "posted")
                    self.log_social_activity(f"✅ Schedule Completed for {target_time_str}")
                else:
                    self.schedule_manager.update_slot_status(date_str, target_time_str, "partial_error")
                
                if wait_seconds <= 0:
                    catchup_count += 1
                
            except Exception as e:
                self.log_social_activity(f"Error in schedule loop: {e}")
                time.sleep(5)

        if self.active_automator:
            try: self.active_automator.close()
            except: pass
            self.active_automator = None

        self.log_social_activity("Schedule Mode Stopped.")
        self.btn_start_post.configure(state="normal", text="🚀 START AUTO-POST")

                                                                                    
                         
                                                                                    
                                                                                 
                                                                                 
                                                                                    
    def start_autopost_process(self):
        if self.post_running:
            self.post_running = False
            self.btn_start_post.configure(text="STOPPING...", fg_color="#F44336")
            self.log_social_activity("Stopping auto-post process...")
            self.close_browser()
            return

                    
        mode = "Interval"
        if hasattr(self, 'var_post_mode'):
            mode = self.var_post_mode.get()

        if mode == "Schedule":
             self.post_running = True
             self.btn_start_post.configure(state="normal", text="STOP POST", fg_color="#D32F2F")
             threading.Thread(target=self.execute_schedule_loop).start()
             return

        selected = [f for f, var in self.queue_vars if var.get()]
        if not selected:
            if self.queue_vars:
                needed = 1
                if self.var_limit_enabled.get():
                    try:
                        limit = int(self.entry_daily_limit.get())
                        posted_today = self.get_daily_post_count()
                        needed = max(1, limit - posted_today)
                    except:
                        needed = 1
                
                             
                target_theme = "All / Random"
                if hasattr(self, 'combo_autopost_theme'):
                     target_theme = self.combo_autopost_theme.get()
                
                is_random_theme = False
                if hasattr(self, 'chk_autopost_random'):
                     is_random_theme = self.chk_autopost_random.get()

                if is_random_theme:
                     _, _, quotes_data, _ = self.load_available_assets()
                     avail_themes = [k for k in quotes_data.keys() if k != "default"]
                     if avail_themes:
                         target_theme = random.choice(avail_themes)
                         self.log_social_activity(f"🎲 Randomly selected theme: {target_theme}")

                selected = []
                count = 0
                
                                         
                candidates = []
                for f, var in self.queue_vars:
                     if target_theme == "All / Random":
                         candidates.append((f, var))
                     else:
                                                                                          
                         v_theme = "Unknown"
                         
                                            
                         json_path = os.path.join(DIRS["output"], f.replace(".mp4", ".json"))
                         if os.path.exists(json_path):
                             try:
                                with open(json_path, 'r', encoding='utf-8') as jf:
                                    dat = json.load(jf)
                                    v_theme = dat.get("theme", "Unknown")
                             except: pass
                         else:
                                                                             
                                                                               
                            if os.path.exists(DIRS["output"]):
                                for item in os.listdir(DIRS["output"]):
                                    theme_dir = os.path.join(DIRS["output"], item)
                                    if os.path.isdir(theme_dir):
                                        meta_file = os.path.join(theme_dir, "metadata.json")
                                        if os.path.exists(meta_file):
                                            try:
                                                with open(meta_file, "r", encoding="utf-8") as jf:
                                                    all_meta = json.load(jf)
                                                    if f in all_meta:
                                                        v_theme = all_meta[f].get("theme", "Unknown")
                                                        break
                                                    elif os.path.basename(f) in all_meta:
                                                        v_theme = all_meta[os.path.basename(f)].get("theme", "Unknown")
                                                        break
                                            except: pass
                                    if v_theme != "Unknown": break

                         if v_theme == target_theme:
                             candidates.append((f, var))

                for f, var in candidates:
                    if count >= needed:
                        break
                    var.set(True)
                    selected.append(f)
                    count += 1
                
                self.log_social_activity(f"Auto-selected {len(selected)} videos from top queue.")
                if len(selected) < needed:
                    self.log_social_activity(f"⚠ WARNING: Queue has only {len(selected)} videos. Need {needed} to reach daily limit.")
                    self.log_social_activity(f"⚠ Please generate more videos!")
            else:
                self.log_social_activity("Error: No videos in queue!")
                return

        self.post_running = True
        self.btn_start_post.configure(state="normal", text="STOP POST", fg_color="#D32F2F")
        threading.Thread(target=self.execute_autopost_queue, args=(selected,)).start()

    def execute_autopost_queue(self, files):
        self.log_social_activity(f"Starting Queue: {len(files)} videos")

        platforms = []
        if self.var_tiktok.get(): platforms.append("TikTok")
        if self.var_ig.get(): platforms.append("Instagram")
        if self.var_yt.get(): platforms.append("Shorts")
        if self.var_fb.get(): platforms.append("Facebook")

        if not platforms:
            self.log_social_activity("Error: No platforms selected!")
            self.post_running = False
            self.btn_start_post.configure(state="normal", text="🚀 START POST", fg_color=self.color_accent)
            return

        posted_history = self.load_posted_history()
        if self.var_limit_enabled.get():
            try:
                limit_str = self.entry_daily_limit.get()
                if "-" in limit_str:
                    l_min, l_max = map(int, limit_str.split("-"))
                    limit = random.randint(l_min, l_max)
                else:
                    limit = int(limit_str)
                    
                posted_today = self.get_daily_post_count()
                if posted_today >= limit:
                    self.log_social_activity(f"Daily Limit Reached ({posted_today}/{limit}). Stopping.")
                    self.post_running = False
                    self.btn_start_post.configure(state="normal", text="🚀 START POST", fg_color=self.color_accent)
                    return
            except ValueError:
                self.log_social_activity("Error: Invalid Daily Limit number.")

        if not SELENIUM_AVAILABLE:
            self.log_social_activity("Error: Selenium not installed. Cannot run.")
            self.post_running = False
            self.btn_start_post.configure(state="normal", text="🚀 START POST", fg_color=self.color_accent)
            return
        else:
            self.log_social_activity("Initializing Chrome for Real Posting...")
            self.active_automator = SocialMediaAutomator(self.log_social_activity, headless=self.var_headless.get())
            if not self.active_automator.start_browser():
                self.log_social_activity("Failed to start browser. Stopping.")
                self.post_running = False
                self.btn_start_post.configure(state="normal", text="🚀 START POST", fg_color=self.color_accent)
                self.active_automator = None
                return

            if not self.active_automator.prepare_sessions(platforms):
                self.log_social_activity("Session preparation failed or cancelled. Stopping.")
                try: self.active_automator.driver.quit()
                except: pass
                self.active_automator = None
                self.post_running = False
                self.btn_start_post.configure(state="normal", text="🚀 START POST", fg_color=self.color_accent)
                return

                                         
              
                                                              
                 
                           

        for idx, filename in enumerate(files):
            if not self.post_running: break
            
                                                
                                                                                        
            if self.var_limit_enabled.get():
                                                                               
                if self.get_daily_post_count() >= limit:
                    self.log_social_activity(f"Daily Limit Reached ({limit}). Stopping.")
                    break
            
                                                            
            last_post_time = self.get_last_post_timestamp()
            if last_post_time:
                try:
                    interval_str = self.entry_interval.get()
                    if "-" in interval_str:
                        i_min, i_max = map(float, interval_str.split("-"))
                        target_interval_mins = (i_min + i_max) / 2                                     
                    else:
                        target_interval_mins = float(interval_str)
                    
                    target_interval_secs = int(target_interval_mins * 60)
                    
                                                            
                    time_diff = datetime.now() - last_post_time
                    seconds_elapsed = time_diff.total_seconds()
                    
                    remaining_wait = target_interval_secs - seconds_elapsed
                    
                    if remaining_wait > 0:
                                            
                        self.log_social_activity(f"⏳ Smart Schedule: Last post was at {last_post_time.strftime('%H:%M')}")
                        
                                                 
                        hours = int(remaining_wait // 3600)
                        mins = int((remaining_wait % 3600) // 60)
                        secs = int(remaining_wait % 60)
                        time_str = f"{hours}h {mins}m {secs}s"
                        
                        self.log_social_activity(f"⏳ Must wait {time_str} to match interval...")
                        
                                   
                        for remaining in range(int(remaining_wait), 0, -1):
                            if not self.post_running: break
                            if remaining % 60 == 0:                          
                                mins_left = remaining // 60
                                self.log_social_activity(f"Next post in {mins_left}m...")
                            time.sleep(1)
                            
                        if not self.post_running: break
                    else:
                        self.log_social_activity(f"✅ Smart Schedule: Safe to post! ({int(seconds_elapsed/60)}m elapsed)")
                        
                except Exception as e:
                    print(f"Smart Schedule Error: {e}")
                                              

            automator = self.active_automator
            if not automator:
                break
            
            file_path = os.path.join(DIRS["output"], filename)
            if not os.path.exists(file_path):
                self.log_social_activity(f"Error: File not found {filename}")
                continue

            self.log_social_activity(f"--- Processing {idx+1}/{len(files)}: {filename} ---")
            caption = self.generate_smart_caption(filename)
            self.log_social_activity(f"Caption: {caption.replace(chr(10), ' ')[:50]}...")

            for p in platforms:
                if (p, filename) in posted_history:
                    self.log_social_activity(f"⚠ Skipping {p}: {filename} (Already posted)")
                    continue

                self.log_social_activity(f"Posting to {p}...")

                status = "Failed"
                link = ""
                res = "Unknown Platform"
                if p == "TikTok":
                    res = automator.upload_tiktok(os.path.abspath(file_path), caption)
                elif p == "Instagram":
                    res = automator.upload_instagram(os.path.abspath(file_path), caption)
                elif p == "Shorts":
                    res = automator.upload_shorts(os.path.abspath(file_path), caption)
                elif p == "Facebook":
                    res = automator.upload_facebook(os.path.abspath(file_path), caption)

                if "Manual" in res:
                    self.log_social_activity(f"⚠ {p}: Waiting for manual confirmation (60s)...")
                    for _ in range(60):
                        if not self.post_running: break
                        time.sleep(1)
                    status = "Manual Check"
                elif "Error" in res:
                    self.log_social_activity(f"❌ {p} Error: {res}")
                    status = "Error"
                else:
                    status = "Success"

                if status in ["Success", "Manual Check"]:
                    self.save_post_log_file(p, filename, status, link)
                    self.increment_daily_count()

            if idx < len(files) - 1:
                try:
                    interval_str = self.entry_interval.get()
                    if "-" in interval_str:
                        i_min, i_max = map(float, interval_str.split("-"))
                        wait_minutes = random.uniform(i_min, i_max)
                    else:
                        base_wait = float(interval_str)
                                                                    
                        jitter = base_wait * 0.1
                        wait_minutes = random.uniform(base_wait - jitter, base_wait + jitter)
                    
                    wait_time = int(wait_minutes * 60)
                except:
                    wait_time = 60
                
                                         
                hours = wait_time // 3600
                mins = (wait_time % 3600) // 60
                secs = wait_time % 60
                time_str = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"

                self.log_social_activity(f"💤 Sleeping {time_str} (Randomized) before next post...")
                for remaining in range(wait_time, 0, -1):
                    if not self.post_running:
                        break

                    self.log_social_activity(f"Next post in {remaining}s...")
                    time.sleep(1)

        if automator:
            self.log_social_activity("Closing Browser...")
            automator.close()

        self.log_social_activity("Queue Finished!")
        self.post_running = False
        self.btn_start_post.configure(state="normal", text="🚀 START AUTO-POST")

    def get_last_post_timestamp(self):
        log_file = os.path.join("config", "social_history.json")
        if not os.path.exists(log_file):
            return None

        today_str = datetime.now().strftime("%Y-%m-%d")
        last_time = None
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    today_posts = [entry for entry in data if entry.get("timestamp", "").startswith(today_str) and entry.get("status") == "Success"]
                    if today_posts:
                        today_posts.sort(key=lambda x: x.get("timestamp"), reverse=True)
                        last_ts_str = today_posts[0].get("timestamp")
                        last_time = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
        except:
            pass
        return last_time

    def get_daily_post_count(self):
        log_file = os.path.join("config", "social_history.json")
        if not os.path.exists(log_file):
            return 0

        today_str = datetime.now().strftime("%Y-%m-%d")
        unique_posted_files = set()
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        ts = entry.get("timestamp", "")
                        status = entry.get("status", "")
                        filename = entry.get("filename", "")
                        if ts.startswith(today_str) and status == "Success":
                            unique_posted_files.add(filename)
        except:
            pass
        return len(unique_posted_files)

    def update_post_count_label(self):
        count = self.get_daily_post_count()
        try:
            limit_str = self.entry_daily_limit.get()
            self.lbl_post_count.configure(text=f"Posted Today: {count} / {limit_str}")
        except:
            self.lbl_post_count.configure(text=f"Posted Today: {count}")

    def increment_daily_count(self):
        self.after(500, self.update_post_count_label)

    def on_click_generate_schedule(self):
        try:
            start_day = int(self.entry_sched_day.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Start Day")
            return

        files = []
        if os.path.exists(DIRS["output"]):
            for root, dirs, filenames in os.walk(DIRS["output"]):
                for filename in filenames:
                    if filename.lower().endswith('.mp4'):
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, DIRS["output"])
                        files.append(rel_path)

        posted_history = self.load_posted_history()
        posted_filenames = {fname for _, fname in posted_history}
        
        available_files = []
        for f in files:
            if f not in posted_filenames and os.path.basename(f) not in posted_filenames:
                available_files.append(f)
        
        if not available_files:
            messagebox.showwarning("Warning", "No available (unposted) MP4 files found in output directory to schedule.")
            return

        count, last_day = self.schedule_manager.generate_monthly_plan(start_day, available_files)
        
        self.log_social_activity(f"📅 Generated schedule for {count} slots starting from day {start_day}.")
        messagebox.showinfo("Success", f"Schedule generated!\n{count} slots filled.")

    def on_click_view_schedule(self):
        try:
            CalendarView(self, self.schedule_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open calendar view:\n{e}")
                                      
            try:
                 path = os.path.abspath(self.schedule_manager.schedule_file)
                 if os.path.exists(path):
                     os.startfile(path)
            except: pass

    def generate_smart_caption(self, filename):
        json_path = os.path.join(DIRS["output"], filename.replace(".mp4", ".json"))
        hook = "Must Watch"
        theme = "love"

        data = {}
        found_data = False

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    found_data = True
            except: pass
        
        if not found_data:
            if os.path.exists(DIRS["output"]):
                for item in os.listdir(DIRS["output"]):
                    theme_dir = os.path.join(DIRS["output"], item)
                    if os.path.isdir(theme_dir):
                        meta_file = os.path.join(theme_dir, "metadata.json")
                        if os.path.exists(meta_file):
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    all_meta = json.load(f)
                                    target_name = os.path.basename(filename)
                                    if target_name in all_meta:
                                        data = all_meta[target_name]
                                        found_data = True
                                        break
                            except: pass
                    if found_data: break

        if found_data:
            hook = data.get("hook", hook)
            theme = data.get("theme", theme)
        
        try:
            if hasattr(self, 'var_show_hook') and not self.var_show_hook.get():
                hook = ""
        except:
            pass
            
        assets_path = os.path.join("config", "caption_assets.json")
        assets = {}
        try:
            if os.path.exists(assets_path):
                with open(assets_path, "r", encoding="utf-8") as f:
                    assets = json.load(f)
        except Exception as e:
            pass

                                      
        theme_key = (theme or "").strip().lower().replace(" ", "_")
        theme_alias = {
            "love": "love",
            "sad": "sad",
            "life": "life",
            "business": "business",
            "motivation": "motivation",
            "nature": "nature",
            "dark": "dark"
        }
        theme_key = theme_alias.get(theme_key, theme_key)
        theme_assets = assets.get(theme_key, assets.get("default", {}))
        
                                                                              
        if not theme_assets:
             theme_assets = assets.get("default", {})

                                                                  
        raw_captions = theme_assets.get("captions", [])
        if not raw_captions:
            raw_captions = theme_assets.get("openings", [])

        caption_text = ""
        if raw_captions:
                                                     
            caption_template = random.choice(raw_captions)
            caption_text = caption_template.replace("{hook}", hook).strip()

                             
        text_parts = []
                                                                                       
        if hook and hook.lower() not in caption_text.lower():
            text_parts.append(hook)
        
        if caption_text:
            text_parts.append(caption_text)
            
        if not text_parts:
            opening_line = caption_text.strip() if caption_text else hook.strip()
        else:
            opening_line = "\n".join(text_parts)

                                           
        all_tags = [t.strip() for t in theme_assets.get("tags", []) if t]
        if not all_tags:
            all_tags = ["#fyp", "#viral", "#trending"]
        
                                                                           
        max_tags = 30
        tags_line = " ".join(all_tags[:max_tags])
        
        if tags_line:
            final_caption = f"{opening_line}\n\n{tags_line}"
        else:
            final_caption = opening_line
        return final_caption

    def _deprecated_generate_caption(self, filename):
        return self.generate_smart_caption(filename)

    def auto_load_latest_preview(self):
        try:
            files = []
            for root, dirs, filenames in os.walk(DIRS["output"]):
                for filename in filenames:
                    if filename.lower().endswith(('.mp4', '.avi', '.mov')):
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, DIRS["output"])
                        files.append(rel_path)

            if files:
                files.sort(key=lambda x: os.path.getmtime(os.path.join(DIRS["output"], x)), reverse=True)
                latest_file = files[0]
                self.video_player.load_video(os.path.join(DIRS["output"], latest_file))
                self.log(f"Auto-loaded preview: {latest_file}")
        except Exception as e:
            pass

    def select_videos_in_queue_by_quantity(self):
        try:
            qty = int(self.entry_sel_qty.get())
        except:
            return

        for _, var in self.queue_vars:
            var.set(False)

        for i in range(min(qty, len(self.queue_vars))):
            self.queue_vars[i][1].set(True)

    def preview_selected_video_thumbnail(self):
        selected = [f for f, var in self.queue_vars if var.get()]
        if not selected:
            if self.queue_vars:
                import random
                rand_item = random.choice(self.queue_vars)
                rand_item[1].set(True)
                selected = [rand_item[0]]
                self.log(f"Randomly selected for preview: {rand_item[0]}")
            else:
                self.video_player.clear("No videos available")
                return

        filename = selected[0]
        path = os.path.join(DIRS["output"], filename)

        if os.path.exists(path):
            self.video_player.load_video(path)
        else:
            self.video_player.clear("File not found")

    def load_video_preview_thumbnail(self, path):
        pass

    def append_to_history(self, meta_data):
        history_file = DIRS["history"]
        history_data = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    if not isinstance(history_data, list):
                        history_data = []
            except:
                history_data = []
        
        history_data.append(meta_data)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            pass

    def consolidate_old_json_files(self):
        if not os.path.exists(DIRS["output"]): return
        json_files = [f for f in os.listdir(DIRS["output"]) if f.endswith(".json")]
        if not json_files: return
        history_file = DIRS["history"]
        history_data = []
        
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    if not isinstance(history_data, list):
                        history_data = []
            except:
                history_data = []
        
        count = 0
        for jf in json_files:
            path = os.path.join(DIRS["output"], jf)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "file" not in data:
                        data["file"] = jf.replace(".json", ".mp4")
                    
                    history_data.append(data)
                os.remove(path)
                count += 1
            except:
                pass
                
        if count > 0:
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(history_data, f, ensure_ascii=False, indent=4)
                self.log(f"Consolidated {count} JSON log files into history.")
            except Exception as e:
                self.log(f"Error saving consolidated history: {e}")

    def save_post_log_file(self, platform, filename, status, link=""):
        json_log_file = os.path.join("config", "social_history.json")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        json_data = {
            "timestamp": ts,
            "platform": platform,
            "filename": filename,
            "status": status,
            "link": link
        }

        try:
            history_data = []
            if os.path.exists(json_log_file):
                try:
                    with open(json_log_file, "r", encoding="utf-8") as f:
                        history_data = json.load(f)
                except:
                    history_data = []
                    
            if not isinstance(history_data, list):
                history_data = []

            history_data.append(json_data)

            with open(json_log_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def check_corrupted_videos(self):
        output_dir = DIRS["output"]
        if not os.path.exists(output_dir):
            self.log_social_activity("Output directory not found.")
            return

        corrupted = []
        self.btn_check_corrupted.configure(state="disabled", text="Checking...")
        self.update_idletasks()
        files = [f for f in os.listdir(output_dir) if f.lower().endswith(".mp4")]
        
        for f in files:
            path = os.path.join(output_dir, f)
            try:
                if os.path.getsize(path) == 0:
                    corrupted.append(f)
                    continue
                try:
                    with imageio.get_reader(path, 'ffmpeg') as reader:
                        pass
                except:
                    corrupted.append(f)
            except Exception as e:
                corrupted.append(f)

        self.btn_check_corrupted.configure(state="normal", text="Check Corrupted")

        if not corrupted:
            from tkinter import messagebox
            messagebox.showinfo("Result", "No corrupted videos found.")
            return
        
        self.show_corrupted_dialog(corrupted)

    def show_corrupted_dialog(self, corrupted_files):
        top = ctk.CTkToplevel(self)
        top.title("Corrupted Videos Found")
        top.geometry("600x400")
        top.attributes("-topmost", True)
        top.transient(self)
        top.grab_set()

        ctk.CTkLabel(top, text=f"Found {len(corrupted_files)} corrupted videos:", font=("Roboto", 14, "bold")).pack(pady=10)

        textbox = ctk.CTkTextbox(top, width=550, height=250)
        textbox.pack(pady=10)
        textbox.insert("1.0", "\n".join(corrupted_files))
        textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x")

        def delete_and_restore():
            deleted_count = 0
            restored_count = 0
            history_file = DIRS["history"]
            used_quotes_data = {"used_quotes": []}
            
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            used_quotes_data = data
                except: pass
            current_used = set(used_quotes_data.get("used_quotes", []))
            
            for fname in corrupted_files:
                path = os.path.join(DIRS["output"], fname)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        deleted_count += 1
                except: pass

                match = re.match(r"^(.*)_\d{8}_\d{6}\.mp4$", fname)
                if match:
                    file_clean_text = match.group(1)
                    quote_to_remove = None
                    for q in current_used:
                        hook = None 
                        clean_q = q
                        invalid_chars = '<>:"/\\|?*'
                        clean_q = "".join([c for c in clean_q if c not in invalid_chars]).strip()
                        clean_q = clean_q.replace(" ", "_").replace("\n", "")[:50]
                        if not clean_q: clean_q = "love_quote"
                        if clean_q == file_clean_text:
                            quote_to_remove = q
                            break
                    
                    if quote_to_remove:
                        current_used.remove(quote_to_remove)
                        restored_count += 1
                        
            used_quotes_data["used_quotes"] = list(current_used)
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(used_quotes_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                pass

            top.destroy()
            from tkinter import messagebox
            messagebox.showinfo("Success", f"Deleted {deleted_count} files.\nRestored {restored_count} quotes.")

        ctk.CTkButton(btn_frame, text="Delete & Restore Quotes", command=delete_and_restore, fg_color="red", hover_color="#880000").pack(side="right", padx=20)
        ctk.CTkButton(btn_frame, text="Cancel", command=top.destroy, fg_color="gray").pack(side="right", padx=20)

if __name__ == "__main__":
    app = ContentGeneratorApp()
    app.mainloop()