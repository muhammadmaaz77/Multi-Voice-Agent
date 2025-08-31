# 🎙️ Multi-Voice AI Conference System

## Complete Setup Guide

### 1. Prerequisites ✅
- Python 3.11+ installed
- Virtual environment activated
- All Python packages installed (Django, Channels, etc.)

### 2. Install FFmpeg (CRITICAL for Audio Processing)

#### Option A: Manual Download (Recommended)
1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download: "ffmpeg-release-essentials.zip"
3. Extract to: `C:\ffmpeg\`
4. Add to PATH: `C:\ffmpeg\bin`
5. Restart VS Code

#### Option B: Using Package Manager
```powershell
# If you have Chocolatey
choco install ffmpeg

# If you have Scoop
scoop install ffmpeg

# If you have winget
winget install "Gyan.FFmpeg"
```

### 3. Start the Server 🚀

```bash
# Navigate to project directory
cd "C:\Users\Soul\Desktop\Voice Project\Multi-Voice-Agent"

# Start Django server
python manage.py runserver 8000
```

### 4. How to Use the System 🎯

#### Step 1: Open Multiple Browser Windows
- Open 3 different browser windows (or use incognito)
- Go to: `http://127.0.0.1:8000`

#### Step 2: Join the Same Conference Room
**Browser 1 (English Speaker):**
- Name: `John`
- Language: `EN` (English)
- Room ID: `12345` (same for all)
- Click "Join Conference"

**Browser 2 (German Speaker):**
- Name: `Hans`
- Language: `DE` (German)
- Room ID: `12345` (same room)
- Click "Join Conference"

**Browser 3 (Russian Speaker):**
- Name: `Ivan`
- Language: `RU` (Russian)
- Room ID: `12345` (same room)
- Click "Join Conference"

#### Step 3: Test Voice Translation
1. **In Browser 1 (English)**: Hold the 🎤 button and say "Hello, how are you?"
2. **Browser 2 & 3 should receive**: Translated text in German and Russian
3. **Try from each browser** with different languages

### 5. Troubleshooting 🔧

#### Test Each Component:
1. **Debug Page**: Visit `http://127.0.0.1:8000/debug/`
2. **Test Translation**: Check if Groq API is working
3. **Test WebSocket**: Check real-time connection
4. **Test Recording**: Check microphone access

#### Common Issues:

**🔴 "No audio detected"**
- Install ffmpeg properly
- Check microphone permissions
- Try different browser

**🔴 "Translation failed"**
- Check Groq API key in settings.py
- Check internet connection
- Verify API quota

**🔴 "WebSocket connection failed"**
- Restart Django server
- Check port 8000 is available
- Try different browser

### 6. Expected Behavior ✅

When working correctly:
- ✅ Each participant sees others in the participants list
- ✅ Speaking indicator appears when someone talks
- ✅ Original text + translated text appears in real-time
- ✅ No errors in browser console

### 7. System Architecture 🏗️

```
Voice Input → Whisper (Transcription) → GPT (Translation) → Display Text
    ↓                                                            ↑
Browser WebSocket ←→ Django Channels ←→ Conference Room ←→ Other Participants
```

### 8. API Endpoints 📡

- `http://127.0.0.1:8000/` - Main conference UI
- `http://127.0.0.1:8000/debug/` - Debug/testing tools
- `http://127.0.0.1:8000/voice_translator/health/` - Health check
- `http://127.0.0.1:8000/voice_translator/test-translate/` - Test translation

### 9. Configuration ⚙️

Key settings in `voice_backend/settings.py`:
```python
GROQ_API_KEY = 'your_api_key_here'
CHANNELS_LAYERS = {...}  # Redis/Memory backend
```

### 10. Production Deployment 🌐

For production use:
1. Set DEBUG = False
2. Configure proper Redis backend
3. Use HTTPS for WebSockets (WSS)
4. Set up proper domain and SSL
5. Configure CORS properly

---

**Need Help?** Check the debug page first: `http://127.0.0.1:8000/debug/`
