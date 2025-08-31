# 🎙️ Multi-Voice AI Conference System

A real-time voice translation conference application built with Django and WebSockets that enables participants speaking different languages to communicate seamlessly.

## 🌟 Features

- **Real-time Voice Translation**: Speak in your language, others hear it in theirs
- **Multi-language Support**: English, German, Russian, Spanish, French, Chinese, Japanese, Korean
- **Live Conference Rooms**: Join rooms with multiple participants
- **WebSocket Communication**: Real-time audio processing and translation delivery
- **Modern UI**: Clean, professional conference interface
- **AI-Powered**: Uses Groq API (Whisper Turbo + GPT) for transcription and translation

## 🏗️ Architecture

```
Voice Input → Whisper (Transcription) → GPT (Translation) → Live Display
    ↓                                                           ↑
Browser WebSocket ↔ Django Channels ↔ Conference Room ↔ Other Participants
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- FFmpeg (for audio processing)
- Groq API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/muhammadmaaz77/Multi-Voice-Agent.git
   cd Multi-Voice-Agent
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django channels channels-redis djangorestframework
   pip install httpx pydub python-decouple aiofiles
   ```

4. **Install FFmpeg**
   - Download from: https://www.gyan.dev/ffmpeg/builds/
   - Add to system PATH

5. **Configure API Key**
   - Add your Groq API key to `voice_backend/settings.py`:
   ```python
   GROQ_API_KEY = 'your_groq_api_key_here'
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Start the server**
   ```bash
   python manage.py runserver 8000
   ```

## 🎯 Usage

1. **Open multiple browser windows**
   - Window 1: `http://127.0.0.1:8000`
   - Window 2: `http://127.0.0.1:8000` (incognito)
   - Window 3: `http://127.0.0.1:8000` (different browser)

2. **Join the same conference room**
   - Use the same Room ID for all participants
   - Choose different names and languages
   - Click "Join Conference"

3. **Start talking**
   - Hold the microphone button and speak
   - Other participants will see your translated message
   - Release to stop recording

## 🔧 Testing

- **Debug Page**: Visit `http://127.0.0.1:8000/debug/` to test components
- **System Test**: Run `python test_system.py` to verify setup
- **Health Check**: `http://127.0.0.1:8000/voice_translator/health/`

## 🛠️ Development

### Project Structure
```
Multi-Voice-Agent/
├── voice_backend/          # Django project settings
├── voice_translator/       # Translation service and models
├── chat/                   # Conference rooms and WebSocket consumers
├── templates/              # HTML templates
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

### Key Components
- **ConferenceConsumer**: Handles WebSocket connections and voice processing
- **VoiceTranslationService**: Manages Groq API integration
- **Conference Models**: Database models for rooms and participants

## 🌐 API Endpoints

- `GET /` - Main conference interface
- `GET /debug/` - System testing tools
- `GET /voice_translator/health/` - Health check
- `POST /voice_translator/test-translate/` - Test translation
- `WebSocket /ws/conference/{room_id}/` - Real-time conference connection

## 🚀 Deployment

For production deployment:

1. Set `DEBUG = False` in settings
2. Configure Redis for Channels
3. Set up proper domain and SSL
4. Use environment variables for sensitive data
5. Configure static file serving

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the SETUP_GUIDE.md
- **Testing**: Use the debug page for troubleshooting

## 🙏 Acknowledgments

- Groq API for fast AI processing
- Django Channels for WebSocket support
- FFmpeg for audio processing

---

**Made with ❤️ for breaking down language barriers in real-time communication**
