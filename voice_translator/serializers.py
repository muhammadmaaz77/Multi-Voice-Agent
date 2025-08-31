from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Language, Translation, VoiceSession


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'code', 'name', 'flag']


class TranslationSerializer(serializers.ModelSerializer):
    source_language = LanguageSerializer(read_only=True)
    target_language = LanguageSerializer(read_only=True)
    source_language_id = serializers.IntegerField(write_only=True)
    target_language_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Translation
        fields = [
            'id', 'source_language', 'target_language', 'source_language_id', 
            'target_language_id', 'original_text', 'translated_text', 
            'audio_file', 'created_at'
        ]


class VoiceSessionSerializer(serializers.ModelSerializer):
    source_language = LanguageSerializer(read_only=True)
    source_language_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = VoiceSession
        fields = [
            'id', 'session_id', 'audio_file', 'transcription', 
            'source_language', 'source_language_id', 'created_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
