import json
import asyncio
import base64
import tempfile
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from .models import ConferenceRoom, Participant, VoiceMessage, TranslatedAudio
from voice_translator.services import VoiceTranslationService


class ConferenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'conference_{self.room_id}'
        self.participant = None
        self.voice_service = VoiceTranslationService()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Remove participant and notify others
        if self.participant:
            await self.set_participant_offline()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_left',
                    'participant_id': self.participant.participant_id,
                    'participant_name': self.participant.name
                }
            )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'join_conference':
                await self.handle_join_conference(data)
            elif message_type == 'voice_message':
                await self.handle_voice_message(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_join_conference(self, data):
        try:
            participant_name = data.get('participant_name')
            language = data.get('language', 'en')

            # Create or get conference room
            room = await self.get_or_create_room()
            
            # Create or get participant
            self.participant = await self.create_participant(
                room, participant_name, language
            )

            # Send current participants list
            participants = await self.get_participants_list(room)
            await self.send(text_data=json.dumps({
                'type': 'participants_list',
                'participants': participants
            }))

            # Notify others about new participant
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_joined',
                    'participant': {
                        'id': self.participant.participant_id,
                        'name': self.participant.name,
                        'language': self.participant.preferred_language
                    }
                }
            )

            await self.send(text_data=json.dumps({
                'type': 'joined_successfully',
                'participant_id': self.participant.participant_id,
                'room_name': room.room_name
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to join conference: {str(e)}'
            }))

    async def handle_voice_message(self, data):
        try:
            if not self.participant:
                raise Exception('Not joined to conference')

            # Decode base64 audio
            audio_data = base64.b64decode(data.get('audio_data', ''))
            speaker_language = data.get('speaker_language', self.participant.preferred_language)

            if not audio_data:
                raise Exception('No audio data provided')

            print(f"[DEBUG] Processing voice message from {self.participant.name}, audio size: {len(audio_data)} bytes")

            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Set speaking status
                await self.set_speaking_status(True)
                
                # Notify others that participant is speaking
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'speaking_status',
                        'participant_id': self.participant.participant_id,
                        'is_speaking': True
                    }
                )

                print(f"[DEBUG] Starting transcription for {self.participant.name}")

                # Process voice message through the translation pipeline
                with open(temp_file_path, 'rb') as audio_file:
                    # Get all participants and their languages
                    participants = await self.get_room_participants()
                    
                    # Transcribe the audio first
                    try:
                        transcription_result = await self.voice_service.transcribe_audio_whisper(audio_file)
                        original_text = transcription_result.get('text', '')
                        detected_language = transcription_result.get('language', speaker_language)
                        
                        print(f"[DEBUG] Transcription successful: '{original_text}' (detected: {detected_language})")
                        
                        if not original_text.strip():
                            raise Exception("No speech detected in audio")
                            
                    except Exception as transcribe_error:
                        print(f"[ERROR] Transcription failed: {transcribe_error}")
                        # Send error message to user
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': f'Speech recognition failed: {str(transcribe_error)}'
                        }))
                        return

                    # Save original voice message
                    voice_message = await self.save_voice_message(
                        original_text, detected_language, audio_data
                    )

                    print(f"[DEBUG] Processing translations for {len(participants)} participants")

                    # Translate for each participant
                    translation_count = 0
                    for participant in participants:
                        if participant.participant_id != self.participant.participant_id:
                            target_language = participant.preferred_language
                            
                            try:
                                if detected_language != target_language:
                                    # Translate text
                                    translated_text = await self.voice_service.translate_text_gpt(
                                        original_text, detected_language, target_language
                                    )
                                    print(f"[DEBUG] Translated to {target_language}: '{translated_text}'")
                                else:
                                    translated_text = original_text
                                    print(f"[DEBUG] No translation needed for {target_language}")

                                # Send translation to specific participant
                                await self.channel_layer.group_send(
                                    self.room_group_name,
                                    {
                                        'type': 'voice_translation',
                                        'target_participant_id': participant.participant_id,
                                        'speaker_name': self.participant.name,
                                        'speaker_id': self.participant.participant_id,
                                        'original_text': original_text,
                                        'translated_text': translated_text,
                                        'original_language': detected_language,
                                        'target_language': target_language,
                                        'voice_message_id': voice_message.message_id
                                    }
                                )
                                translation_count += 1
                                
                            except Exception as translate_error:
                                print(f"[ERROR] Translation failed for {participant.name}: {translate_error}")
                                # Send translation error to specific participant
                                await self.channel_layer.group_send(
                                    self.room_group_name,
                                    {
                                        'type': 'voice_translation',
                                        'target_participant_id': participant.participant_id,
                                        'speaker_name': self.participant.name,
                                        'speaker_id': self.participant.participant_id,
                                        'original_text': original_text,
                                        'translated_text': f"[Translation Error: {str(translate_error)}]",
                                        'original_language': detected_language,
                                        'target_language': target_language,
                                        'voice_message_id': voice_message.message_id,
                                        'error': True
                                    }
                                )

                    print(f"[DEBUG] Sent {translation_count} translations")

                # Set speaking status to false
                await self.set_speaking_status(False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'speaking_status',
                        'participant_id': self.participant.participant_id,
                        'is_speaking': False
                    }
                )

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            print(f"[ERROR] Voice message processing failed: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Voice processing failed: {str(e)}'
            }))

    # WebSocket message handlers
    async def participant_joined(self, event):
        await self.send(text_data=json.dumps(event))

    async def participant_left(self, event):
        await self.send(text_data=json.dumps(event))

    async def speaking_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def voice_translation(self, event):
        # Only send to the target participant
        if (hasattr(self, 'participant') and self.participant and 
            event.get('target_participant_id') == self.participant.participant_id):
            await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def get_or_create_room(self):
        room, created = ConferenceRoom.objects.get_or_create(
            room_id=self.room_id,
            defaults={
                'room_name': f'Conference Room {self.room_id}',
                'is_active': True
            }
        )
        return room

    @database_sync_to_async
    def create_participant(self, room, name, language):
        # Check if participant with same name exists in room
        try:
            participant = Participant.objects.get(name=name, room=room)
            participant.is_online = True
            participant.preferred_language = language
            participant.save()
            return participant
        except Participant.DoesNotExist:
            return Participant.objects.create(
                name=name,
                room=room,
                preferred_language=language,
                is_online=True
            )

    @database_sync_to_async
    def get_participants_list(self, room):
        participants = room.participants.filter(is_online=True)
        return [
            {
                'id': p.participant_id,
                'name': p.name,
                'language': p.preferred_language,
                'is_speaking': p.is_speaking
            }
            for p in participants
        ]

    @database_sync_to_async
    def get_room_participants(self):
        if not self.participant:
            return []
        return list(self.participant.room.participants.filter(is_online=True))

    @database_sync_to_async
    def save_voice_message(self, original_text, detected_language, audio_data):
        # Save audio file
        audio_file = ContentFile(audio_data, name=f'voice_{self.participant.participant_id}.wav')
        
        return VoiceMessage.objects.create(
            room=self.participant.room,
            speaker=self.participant,
            original_audio_file=audio_file,
            original_text=original_text,
            detected_language=detected_language
        )

    @database_sync_to_async
    def set_speaking_status(self, is_speaking):
        if self.participant:
            self.participant.is_speaking = is_speaking
            self.participant.save()

    @database_sync_to_async
    def set_participant_offline(self):
        if self.participant:
            self.participant.is_online = False
            self.participant.is_speaking = False
            self.participant.save()
