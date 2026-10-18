@echo off
chcp 65001 >nul
echo ============================================
echo  🏭 Auto Knowledge Factory
echo  โรงงานรู้หรือไม่ใน 1 นาที - อัตโนมัติ
echo ============================================
echo.

REM ตรวจ venv หรือ pip
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ไม่เจอ Python - ติดตั้ง Python 3.10+ ก่อน
    pause
    exit /b
)

echo [1] ตรวจวัตถุดิบ
python auto_factory.py --check-assets
echo.

echo [2] ผลิต 2 คลิป + ตั้งเวลา
python auto_factory.py --daily --batch 2
echo.

echo [3] รายงาน
python -m factory.analytics
echo.

echo ✅ เสร็จ! ดูไฟล์ที่ outputs/knowledge/
echo กด Enter เพื่อเปิดโฟลเดอร์
pause >nul
explorer outputs\knowledge
pause
