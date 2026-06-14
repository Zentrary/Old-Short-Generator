# Content Generator

Content Generator is a desktop app for creating social media video content from theme-based assets. It combines quote and hook management, AI writing, media previewing, video generation, and optional auto-posting into one CustomTkinter interface.

## Features

- Generate short-form videos from quotes, hooks, background images, and music
- Preview output inside the app before exporting
- Manage quotes and hooks in the built-in asset editor
- Generate new quotes or hooks with Groq-powered AI writing
- Download backgrounds and music from external asset sources
- Render Thai text correctly with dedicated text handling helpers
- Configure captions, fonts, filters, volume, duration, and other settings
- Auto-post to supported platforms through Selenium-based automation
- Build monthly posting schedules and track posting history

## Project Structure

- `main.py` - main application entry point and all application logic
- `assets/` - backgrounds, fonts, images, and music folders used by the generator
- `config/` - JSON files for quotes, hooks, history, schedules, settings, and social history
- `run.bat` - convenience launcher for Windows

## Requirements

The app uses a mix of required and optional Python packages, including:

- customtkinter
- pillow
- numpy
- imageio
- requests
- cloudscraper
- groq
- pygame
- edge_tts
- beautifulsoup4
- moviepy
- selenium
- webdriver-manager

Some features such as browser automation, TTS, and video composition depend on optional packages.

## Setup

1. Install the Python dependencies used by the app.
2. Add your fonts, background images, and music files into the folders under `assets/`.
3. Update the JSON files in `config/` if you want to change default assets or settings.
4. Run `main.py` or use `run.bat` on Windows.

## Notes

- API keys and account settings are stored in the JSON config files.
- The app is designed around theme-based content such as Business, Dark, Life, Love, Motivation, Nature, and Sad.
