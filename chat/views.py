from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import ConferenceRoom, Participant, VoiceMessage


@api_view(['GET'])
def health_check(request):
    """Health check for chat service"""
    return Response({
        'status': 'healthy',
        'message': 'Conference service is running'
    })


@api_view(['GET'])
def list_rooms(request):
    """List all active conference rooms"""
    try:
        rooms = ConferenceRoom.objects.filter(is_active=True)
        rooms_data = []
        
        for room in rooms:
            rooms_data.append({
                'room_id': room.room_id,
                'room_name': room.room_name,
                'participant_count': room.participants.filter(is_online=True).count(),
                'created_at': room.created_at
            })
        
        return Response(rooms_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_room(request):
    """Create a new conference room"""
    try:
        room_name = request.data.get('room_name', 'New Conference Room')
        
        room = ConferenceRoom.objects.create(
            room_name=room_name
        )
        
        return Response({
            'room_id': room.room_id,
            'room_name': room.room_name,
            'message': 'Conference room created successfully'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def room_participants(request, room_id):
    """Get participants in a specific room"""
    try:
        room = get_object_or_404(ConferenceRoom, room_id=room_id)
        participants = room.participants.filter(is_online=True)
        
        participants_data = []
        for participant in participants:
            participants_data.append({
                'participant_id': participant.participant_id,
                'name': participant.name,
                'language': participant.preferred_language,
                'is_speaking': participant.is_speaking,
                'joined_at': participant.joined_at
            })
        
        return Response({
            'room_id': room_id,
            'participants': participants_data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
