"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from backend_app.views import MessageView, UserAuthView, UserLogoutView, FriendChatDeleteView,FriendRequestDeleteView,MessageDeleteView,GroupChatDeleteView,GroupInviteCodeDeleteView,GroupInvitePrivateDeleteView,FriendChatView,GroupChatView, set_csrf_token, FriendAdd,EmptyChatView, CreateGroupInvite, CreateFriendRequest, GetFriendChatId,GetGroupChatId
from django.views.generic import TemplateView

urlpatterns = [
    path('messages/', MessageView.as_view(), name='messages'),
    path('message_form/', TemplateView.as_view(template_name='message_form.html'), name='message_form'),
    path('auth/', UserAuthView.as_view(), name='auth'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('chat/f/<int:pk>/', FriendChatView, name='friend_chat'),
    path('chat/g/<int:pk>/', GroupChatView, name='group_chat'),
    path('chat/',EmptyChatView, name="empty_chat"),
    path('friend/',FriendAdd,name="add_friend"),
    path('csrf/', set_csrf_token, name='set_csrf_token'),
    path('group_code/create/<int:pk>/',CreateGroupInvite,name="group_code_create"),
    path('friend_code/create/',CreateFriendRequest,name="friend_code_create"),
    path('chat/friend/get/<int:pk>/',GetFriendChatId,name="get_friend_chat_id"),
    path('chat/group/get/<int:pk>/',GetGroupChatId,name="get_group_chat_id"),

    #for development purposes
    path('friend/delete/', FriendChatDeleteView.as_view(),name="friend_delete"),
    path('group/delete/', GroupChatDeleteView.as_view(),name="group_delete"),
    path('message/delete/', MessageDeleteView.as_view(),name="message_delete"),
    path('friend_request/delete/', FriendRequestDeleteView.as_view(),name="friend_request_delete"),
    path('group_code/delete/',GroupInviteCodeDeleteView.as_view(),name="group_code_delete"),
    path('group_private/delete/',GroupInvitePrivateDeleteView.as_view(),name="group_private_delete")
]