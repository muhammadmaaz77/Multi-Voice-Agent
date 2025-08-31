#!/usr/bin/env python
"""
Quick system test for Multi-Voice AI Conference
"""
import os
import sys
import django
import asyncio

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_backend.settings')
django.setup()

from voice_translator.services import VoiceTranslationService
from django.conf import settings

def test_basic_setup():
    """Test basic Django setup"""
    print("🔧 Testing Django setup...")
    
    # Check if settings are loaded
    try:
        secret_key = settings.SECRET_KEY
        print("✅ Django settings loaded")
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return False
    
    # Check if Groq API key is set
    try:
        api_key = settings.GROQ_API_KEY
        if api_key and len(api_key) > 10:
            print("✅ Groq API key configured")
        else:
            print("❌ Groq API key not properly configured")
            return False
    except Exception as e:
        print(f"❌ Groq API key error: {e}")
        return False
    
    return True

async def test_translation_service():
    """Test the translation service"""
    print("\n🌐 Testing translation service...")
    
    try:
        service = VoiceTranslationService()
        
        # Test text translation
        result = await service.translate_text_gpt(
            "Hello, how are you?", 
            "en", 
            "de"
        )
        
        if result and len(result) > 0:
            print(f"✅ Translation successful: '{result}'")
            return True
        else:
            print("❌ Translation returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        return False

def test_ffmpeg():
    """Test if ffmpeg is available"""
    print("\n🎵 Testing FFmpeg...")
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is available")
            return True
        else:
            print("❌ FFmpeg not working properly")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        print("   Please install from: https://www.gyan.dev/ffmpeg/builds/")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def test_dependencies():
    """Test Python dependencies"""
    print("\n📦 Testing Python dependencies...")
    
    required_packages = [
        'django',
        'channels',
        'rest_framework',
        'httpx',
        'pydub'
    ]
    
    all_good = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            all_good = False
    
    return all_good

def main():
    print("=" * 50)
    print("   Multi-Voice AI Conference - System Test")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_basic_setup():
        tests_passed += 1
    
    if test_dependencies():
        tests_passed += 1
    
    if test_ffmpeg():
        tests_passed += 1
    
    # Test translation (async)
    try:
        if asyncio.run(test_translation_service()):
            tests_passed += 1
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"   Test Results: {tests_passed}/{total_tests} passed")
    print("=" * 50)
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver 8000")
        print("2. Open: http://127.0.0.1:8000")
        print("3. Test with multiple browser windows")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nFor help:")
        print("1. Check the SETUP_GUIDE.md file")
        print("2. Visit: http://127.0.0.1:8000/debug/ (when server is running)")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
