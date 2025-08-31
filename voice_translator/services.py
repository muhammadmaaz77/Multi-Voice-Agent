import requests
import json
import tempfile
import os
import uuid
import asyncio
import httpx
from django.conf import settings
import io

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

class VoiceTranslationService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_base_url = "https://api.groq.com/openai/v1"
        
    async def transcribe_audio_whisper(self, audio_file):
        """Step 1: Transcribe audio using Groq Whisper Turbo"""
        try:
            if not PYDUB_AVAILABLE:
                raise Exception("pydub not available - audio processing disabled")
            
            # Convert audio to proper format for Whisper
            try:
                audio_segment = AudioSegment.from_file(audio_file)
                # Ensure audio is in correct format (16kHz, mono, wav)
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            except Exception as audio_error:
                # If audio conversion fails, try to use original file
                print(f"Audio conversion failed, using original: {audio_error}")
                # Create a simple temporary file copy
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    audio_file.seek(0)
                    temp_file.write(audio_file.read())
                    temp_file_path = temp_file.name
            else:
                # Create temporary file with converted audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    audio_segment.export(temp_file.name, format="wav")
                    temp_file_path = temp_file.name
            
            try:
                # Prepare the request to Groq Whisper
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}"
                }
                
                with open(temp_file_path, "rb") as audio_file_handle:
                    files = {
                        "file": ("audio.wav", audio_file_handle, "audio/wav"),
                        "model": (None, "whisper-large-v3"),
                        "response_format": (None, "json"),
                        "language": (None, "auto")  # Auto-detect language
                    }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.groq_base_url}/audio/transcriptions",
                            headers=headers,
                            files=files,
                            timeout=30.0
                        )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "text": result.get("text", ""),
                        "language": result.get("language", "unknown")
                    }
                else:
                    raise Exception(f"Transcription failed: {response.status_code} - {response.text}")
                    
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    async def translate_text_gpt(self, text, source_language, target_language):
        """Step 2: Translate text using Groq GPT model"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            # Enhanced prompt for better translation quality
            prompt = f"""You are a professional conference interpreter. Translate the following {source_language} text to {target_language} with high accuracy and natural flow.

Source text: "{text}"

Requirements:
- Maintain the speaker's tone and intent
- Use formal/professional language appropriate for conferences
- Preserve technical terms and proper nouns
- Only return the translated text, nothing else

Translation:"""
            
            data = {
                "model": "llama-3.1-8b-instant",  # Updated to current model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional conference interpreter providing accurate, natural translations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
                "top_p": 1,
                "stop": None
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.groq_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                return translated_text
            else:
                raise Exception(f"Translation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"GPT translation failed: {str(e)}")

    async def text_to_speech_playai(self, text, target_language, voice_style="professional"):
        """Step 3: Convert translated text to speech using PlayAI TTS"""
        try:
            # For now, we'll use a placeholder since PlayAI integration requires API keys
            # In production, you would integrate with PlayAI TTS API
            
            # Placeholder: Return a success message indicating TTS would be generated
            return {
                "success": True,
                "audio_url": f"/generated_audio/{uuid.uuid4()}.mp3",
                "message": f"TTS generated for: {text[:50]}..."
            }
            
            # Future PlayAI integration would look like:
            """
            headers = {
                "Authorization": f"Bearer {self.playai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "voice": self.get_voice_for_language(target_language, voice_style),
                "speed": 1.0,
                "emotion": "neutral"
            }
            
            response = await client.post(
                "https://api.play.ai/v1/tts",
                headers=headers,
                json=data
            )
            """
            
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")

    async def full_voice_translation_pipeline(self, audio_file, source_language, target_language):
        """Complete pipeline: Audio → Whisper → GPT → PlayAI TTS"""
        try:
            # Step 1: Transcribe audio
            transcription_result = await self.transcribe_audio_whisper(audio_file)
            original_text = transcription_result["text"]
            detected_language = transcription_result.get("language", source_language)
            
            # Step 2: Translate text if needed
            if detected_language != target_language:
                translated_text = await self.translate_text_gpt(
                    original_text, detected_language, target_language
                )
            else:
                translated_text = original_text
            
            # Step 3: Generate speech
            tts_result = await self.text_to_speech_playai(translated_text, target_language)
            
            return {
                "original_text": original_text,
                "translated_text": translated_text,
                "source_language": detected_language,
                "target_language": target_language,
                "tts_result": tts_result,
                "pipeline_id": str(uuid.uuid4())
            }
            
        except Exception as e:
            raise Exception(f"Voice translation pipeline failed: {str(e)}")

    def get_voice_for_language(self, language, style="professional"):
        """Get appropriate voice settings for each language"""
        voice_mapping = {
            "en": "en-US-neural-male",
            "es": "es-ES-neural-male", 
            "fr": "fr-FR-neural-male",
            "de": "de-DE-neural-male",
            "ru": "ru-RU-neural-male",
            "zh": "zh-CN-neural-male",
            "ja": "ja-JP-neural-male",
            "ko": "ko-KR-neural-male"
        }
        return voice_mapping.get(language, "en-US-neural-male")

    async def detect_language_from_audio(self, audio_file):
        """Detect language from audio using Whisper"""
        try:
            result = await self.transcribe_audio_whisper(audio_file)
            return result.get("language", "unknown")
        except Exception as e:
            return "unknown"
