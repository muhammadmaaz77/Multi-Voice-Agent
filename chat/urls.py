from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('rooms/', views.list_rooms, name='list-rooms'),
    path('rooms/create/', views.create_room, name='create-room'),
    path('rooms/<str:room_id>/participants/', views.room_participants, name='room-participants'),
]
