@echo off
echo ==========================================
echo    Multi-Voice AI Conference System
echo ==========================================

echo.
echo Checking requirements...

REM Check if we're in the right directory
if not exist "manage.py" (
    echo ERROR: Please run this script from the Multi-Voice-Agent directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo ✓ Found manage.py

REM Check if virtual environment is available
if not exist "C:\Users\Soul\Desktop\Voice Project\.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please ensure the virtual environment is set up at:
    echo C:\Users\Soul\Desktop\Voice Project\.venv\
    pause
    exit /b 1
)

echo ✓ Found virtual environment

REM Check for ffmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  WARNING: FFmpeg not found in PATH
    echo Voice translation may not work properly
    echo Please install FFmpeg: https://www.gyan.dev/ffmpeg/builds/
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

echo ✓ FFmpeg check completed

echo.
echo Starting Django server...
echo.
echo 🚀 Server will start at: http://127.0.0.1:8000
echo 🔧 Debug page available at: http://127.0.0.1:8000/debug/
echo.
echo Press Ctrl+C to stop the server
echo.

"C:\Users\Soul\Desktop\Voice Project\.venv\Scripts\python.exe" manage.py runserver 8000

echo.
echo Server stopped.
pause
