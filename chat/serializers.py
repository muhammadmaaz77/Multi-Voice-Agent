from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message, UserPresence
from voice_translator.serializers import LanguageSerializer, UserSerializer


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'description', 'participants', 'participant_count', 'created_at', 'is_active']

    def get_participant_count(self, obj):
        return obj.participants.count()


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    original_language = LanguageSerializer(read_only=True)
    original_language_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'user', 'message_type', 'content', 
            'original_language', 'original_language_id', 'translated_content', 
            'audio_file', 'timestamp'
        ]


class UserPresenceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = ChatRoomSerializer(read_only=True)
    current_language = LanguageSerializer(read_only=True)

    class Meta:
        model = UserPresence
        fields = ['user', 'room', 'is_online', 'last_seen', 'current_language']
