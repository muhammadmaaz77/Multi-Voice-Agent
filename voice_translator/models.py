from django.db import models
from django.contrib.auth.models import User


class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    flag = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Translation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='source_translations')
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='target_translations')
    original_text = models.TextField()
    translated_text = models.TextField()
    audio_file = models.FileField(upload_to='audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_language.code} -> {self.target_language.code}: {self.original_text[:50]}"


class VoiceSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    audio_file = models.FileField(upload_to='recordings/')
    transcription = models.TextField(blank=True)
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.source_language.code}"
