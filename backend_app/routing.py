from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/f/chat/(?P<room_name>\w+)/$", consumers.FriendChatConsumer.as_asgi()),
    re_path(r"ws/g/chat/(?P<room_name>\w+)/$", consumers.GroupChatConsumer.as_asgi()),
    re_path(r"ws/communicate/$", consumers.CommunicateConsumer.as_asgi())
]