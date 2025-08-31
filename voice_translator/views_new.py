from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

from .models import Language
from .serializers import LanguageSerializer


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
    """Simple test endpoint for translation"""
    try:
        text = request.data.get('text', '')
        source_lang = request.data.get('source_language', 'en')
        target_lang = request.data.get('target_language', 'es')
        
        if not text:
            return Response(
                {'error': 'Text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For now, return a mock translation
        # In production, this would use the VoiceTranslationService
        mock_translation = f"[{target_lang.upper()}] {text}"

        return Response({
            'original_text': text,
            'translated_text': mock_translation,
            'source_language': source_lang,
            'target_language': target_lang,
            'note': 'This is a test endpoint. Real translation happens via WebSocket.'
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
