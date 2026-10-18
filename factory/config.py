"""
config.py - โหลดการตั้งค่าโรงงาน + ความรู้
"""
import json
import os

FACTORY_SETTINGS_PATH = "config/factory_settings.json"
KNOWLEDGE_PATH = "config/knowledge.json"
SETTINGS_PATH = "config/settings.json"

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default or {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_factory_settings():
    return load_json(FACTORY_SETTINGS_PATH, {})

def get_knowledge():
    return load_json(KNOWLEDGE_PATH, {})

def get_settings():
    return load_json(SETTINGS_PATH, {})

def get_groq_key():
    s = get_settings()
    return s.get("groq_api_key", "")

def get_pexels_key():
    s = get_settings()
    return s.get("pexels_key", "")

def get_pixabay_key():
    s = get_settings()
    return s.get("pixabay_key", "")
