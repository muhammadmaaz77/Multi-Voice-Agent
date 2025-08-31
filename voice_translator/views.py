from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import asyncio

from .models import Language
from .serializers import LanguageSerializer
from .services import VoiceTranslationService


class LanguageListView(generics.ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'Voice translation API is running'
    })


@api_view(['POST'])
def test_translation(request):
    """Test endpoint for translation using real Groq API"""
    try:
        text = request.data.get('text', '')
        source_lang = request.data.get('source_language', 'en')
        target_lang = request.data.get('target_language', 'es')
        
        if not text:
            return Response(
                {'error': 'Text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Test real translation service
        service = VoiceTranslationService()
        
        async def test_async():
            try:
                translated_text = await service.translate_text_gpt(text, source_lang, target_lang)
                return translated_text, None
            except Exception as e:
                return None, str(e)
        
        # Run async function
        translated_text, error = asyncio.run(test_async())
        
        if error:
            return Response({
                'error': f'Translation failed: {error}',
                'original_text': text,
                'source_language': source_lang,
                'target_language': target_lang
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'success': True,
            'note': 'Translation via Groq GPT API'
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
