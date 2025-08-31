from django.db import models
import uuid


class ConferenceRoom(models.Model):
    room_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    room_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=20)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.room_id}: {self.room_name}"


class Participant(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('ru', 'Russian'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('ar', 'Arabic'),
        ('hi', 'Hindi'),
    ]

    participant_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    room = models.ForeignKey(ConferenceRoom, on_delete=models.CASCADE, related_name='participants')
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    is_speaking = models.BooleanField(default=False)
    is_online = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'room']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.name} ({self.preferred_language}) in {self.room.room_name}"


class VoiceMessage(models.Model):
    message_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    room = models.ForeignKey(ConferenceRoom, on_delete=models.CASCADE, related_name='voice_messages')
    speaker = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='voice_messages')
    original_audio_file = models.FileField(upload_to='voice_messages/')
    original_text = models.TextField()
    detected_language = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Message from {self.speaker.name} at {self.timestamp}"


class TranslatedAudio(models.Model):
    voice_message = models.ForeignKey(VoiceMessage, on_delete=models.CASCADE, related_name='translations')
    target_participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='received_translations')
    target_language = models.CharField(max_length=10)
    translated_text = models.TextField()
    translated_audio_file = models.FileField(upload_to='translated_audio/', null=True, blank=True)
    translation_status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='processing')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['voice_message', 'target_participant']
        ordering = ['-created_at']

    def __str__(self):
        return f"Translation for {self.target_participant.name} ({self.target_language})"


class ConferenceSession(models.Model):
    session_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    room = models.ForeignKey(ConferenceRoom, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session {self.session_id} in {self.room.room_name}"
