from django.urls import re_path
from . import conference_consumer

websocket_urlpatterns = [
    re_path(r'ws/conference/(?P<room_id>\w+)/$', conference_consumer.ConferenceConsumer.as_asgi()),
]
