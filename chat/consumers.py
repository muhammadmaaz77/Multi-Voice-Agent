import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message, UserPresence
from voice_translator.models import Language
from voice_translator.services import TranslationService


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope.get('user')

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update user presence
        if self.user and self.user.is_authenticated:
            await self.update_user_presence(True)
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user': self.user.username,
                    'user_id': self.user.id
                }
            )

    async def disconnect(self, close_code):
        # Update user presence
        if self.user and self.user.is_authenticated:
            await self.update_user_presence(False)
            
            # Notify others that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user': self.user.username,
                    'user_id': self.user.id
                }
            )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'text_message')

            if message_type == 'text_message':
                await self.handle_text_message(text_data_json)
            elif message_type == 'voice_message':
                await self.handle_voice_message(text_data_json)
            elif message_type == 'translation_request':
                await self.handle_translation_request(text_data_json)
            elif message_type == 'language_change':
                await self.handle_language_change(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_text_message(self, data):
        message = data['message']
        source_language = data.get('source_language', 'en')
        
        if self.user and self.user.is_authenticated:
            # Save message to database
            message_obj = await self.save_message(
                message, 'text', source_language
            )
            
            # Get translations for other languages in the room
            translations = await self.get_translations(message, source_language)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'message_id': message_obj.id if message_obj else None,
                    'source_language': source_language,
                    'translations': translations,
                    'timestamp': message_obj.timestamp.isoformat() if message_obj else None
                }
            )

    async def handle_voice_message(self, data):
        # This would handle voice message processing
        # For now, we'll just echo the message
        message = data.get('transcription', '')
        source_language = data.get('source_language', 'en')
        
        if self.user and self.user.is_authenticated:
            # Save voice message
            message_obj = await self.save_message(
                message, 'voice', source_language
            )
            
            # Get translations
            translations = await self.get_translations(message, source_language)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_message',
                    'message': message,
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'message_id': message_obj.id if message_obj else None,
                    'source_language': source_language,
                    'translations': translations,
                    'timestamp': message_obj.timestamp.isoformat() if message_obj else None
                }
            )

    async def handle_translation_request(self, data):
        text = data.get('text', '')
        source_lang = data.get('source_language', 'en')
        target_lang = data.get('target_language', 'es')
        
        try:
            translation_service = TranslationService()
            translated_text = await database_sync_to_async(
                translation_service.translate_text
            )(text, source_lang, target_lang)
            
            await self.send(text_data=json.dumps({
                'type': 'translation_result',
                'original_text': text,
                'translated_text': translated_text,
                'source_language': source_lang,
                'target_language': target_lang
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Translation failed: {str(e)}'
            }))

    async def handle_language_change(self, data):
        language_code = data.get('language', 'en')
        
        if self.user and self.user.is_authenticated:
            await self.update_user_language(language_code)
            
            # Notify others about language change
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'language_changed',
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'language': language_code
                }
            )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'is_typing': is_typing
                }
            )

    # WebSocket message handlers
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def voice_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_left(self, event):
        await self.send(text_data=json.dumps(event))

    async def language_changed(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        # Don't send typing indicator to the sender
        if event.get('user_id') != (self.user.id if self.user else None):
            await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def save_message(self, content, message_type, source_language):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            
            try:
                language_obj = Language.objects.get(code=source_language)
            except Language.DoesNotExist:
                language_obj = None
            
            return Message.objects.create(
                room=room,
                user=self.user,
                message_type=message_type,
                content=content,
                original_language=language_obj
            )
        except Exception:
            return None

    @database_sync_to_async
    def update_user_presence(self, is_online):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            presence, created = UserPresence.objects.get_or_create(
                user=self.user,
                defaults={'room': room, 'is_online': is_online}
            )
            if not created:
                presence.room = room if is_online else None
                presence.is_online = is_online
                presence.save()
        except Exception:
            pass

    @database_sync_to_async
    def update_user_language(self, language_code):
        try:
            language_obj = Language.objects.get(code=language_code)
            presence, created = UserPresence.objects.get_or_create(
                user=self.user,
                defaults={'current_language': language_obj}
            )
            if not created:
                presence.current_language = language_obj
                presence.save()
        except Exception:
            pass

    @database_sync_to_async
    def get_translations(self, text, source_language):
        try:
            # Get languages used by room participants
            room = ChatRoom.objects.get(id=self.room_id)
            participant_languages = set()
            
            for participant in room.participants.all():
                try:
                    presence = UserPresence.objects.get(user=participant)
                    if presence.current_language:
                        participant_languages.add(presence.current_language.code)
                except UserPresence.DoesNotExist:
                    pass
            
            # Add default languages if none set
            if not participant_languages:
                participant_languages = {'en', 'es', 'fr', 'de'}
            
            # Remove source language
            participant_languages.discard(source_language)
            
            if participant_languages:
                translation_service = TranslationService()
                return translation_service.translate_to_multiple_languages(
                    text, source_language, list(participant_languages)
                )
            
            return {}
        except Exception:
            return {}
