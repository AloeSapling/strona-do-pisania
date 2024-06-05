from backend_app.models import Message, CustomUser, GroupChat, FriendChat, FriendRequestPrivate, FriendRequestCode, GroupInviteCode, GroupInvitePrivate
from django.contrib.auth import authenticate,login,logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from backend_app.forms import MessageForm, UserRegistrationForm, UserLoginForm, FriendChatAdd, GroupChatCreate
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import json
# Create your views here.
def GetLoggedInStuff(user):
    if(user.is_authenticated):
        print("what")
        friend_requests =[
            {"from_user": {"id": request.from_user.id, "username": request.from_user.username}} for request in FriendRequestPrivate.objects.filter(to_user=user)
        ]
        outgoing_friend_requests =[
            {"to_user": {"id": request.to_user.id, "username": request.to_user.username}} for request in FriendRequestPrivate.objects.filter(from_user=user)
        ]
        group_invites =[
            {"id": invite.id, "group": {"name": invite.group.name}} for invite in GroupInvitePrivate.objects.filter(to_user=user)
        ]
        outgoing_group_invites = [
            {"group": {"id": invite.group.id, "name": invite.group.name}} for invite in GroupInvitePrivate.objects.filter(from_user=user)
        ]
        group_chats = [
            {"id": group.id, "name": group.name} for group in GroupChat.objects.filter(users=user)
        ]
        friend_chats_with_other_user = [
            (chat,chat.get_other_user(user)) for chat in FriendChat.objects.filter(users=user)
        ]
        try:
            friend_code = FriendRequestCode.objects.get(user=user).code
        except ObjectDoesNotExist:
            friend_code = "not_found"
        try:
            group_code = GroupInviteCode.objects.get(from_user=user).code
        except ObjectDoesNotExist:
            group_code = "not_found"
        friend_request_user_ids = set(
            [request['from_user']['id'] for request in friend_requests] +
            [request['to_user']['id'] for request in outgoing_friend_requests]
        )
        friend_chat_user_ids = set(
            [other_user.id for _, other_user in friend_chats_with_other_user]
        )
        excluded_user_ids = friend_request_user_ids | friend_chat_user_ids | {user.id}
        users_you_can_friend = [
            {"id": user.id, "username": user.username}
            for user in CustomUser.objects.exclude(id__in=excluded_user_ids)
        ]
        return {
            "friend_chats": friend_chats_with_other_user,
            "incoming_friend_requests": friend_requests,
            "outgoing_friend_requests": outgoing_friend_requests,
            "group_chats": group_chats,
            "incoming_group_invites": group_invites,
            "outgoing_group_invites": outgoing_group_invites,
            "friend_code": friend_code,
            "group_code": group_code,
            'current_user':user,
            'users_you_can_friend': json.dumps(users_you_can_friend)
        }
    else: return {}

def FriendChatView(request,pk):
    if(request.user.is_authenticated):
        chat = get_object_or_404(FriendChat,id=pk)
        messages = []
        messages = chat.messages.all()
        messages = [
            {"id": message.id, "content": message.content, "edited":message.edited, "author": {"username": message.author.username, "id": message.author.id}} for message in chat.messages.all()
        ]
        id = pk
        if(chat.users.filter(id=request.user.id)):
            return render(request, 'friendchat.html', {'id': id,
                                                       'messages':messages,
                                                       **GetLoggedInStuff(request.user)})
        return "error users not friends"
    return "error user is not logged in"
def EmptyChatView(request):
    if(request.user.is_authenticated):
        return render(request, 'emptychat.html',{**GetLoggedInStuff(request.user)})
    return "error user is not logged in"
def GroupChatView(request,pk):
    if(request.user.is_authenticated):
        chat = get_object_or_404(GroupChat,id=pk)
        id = pk
        if(chat.users.filter(id=request.user.id)):
            return render(request, 'groupchat.html', {'id': id,**GetLoggedInStuff(request.user)})
        return "error user not in group"
    return "error user is not logged in"
def CreateGroupInvite(request,pk):
    if(request.user.is_authenticated):
        if(GroupChat.objects.filter(id=pk).exists() == False):
            return {'message': 'group of given id does not exist'}
        group = GroupChat.objects.get(id=pk)
        if(group.users.filter(id=request.user.id).exists() == False):
            return {'message': 'user is not within provided group'}
        if(GroupInviteCode.objects.filter(group=group,from_user=request.user).exists()):
            GroupInviteCode.objects.get(group=group,from_user=request.user).delete()
        invite = GroupInviteCode.objects.create(group=group,from_user=request.user)
        invite.save()
        return JsonResponse({'code': invite.code})
    return {'message': 'user not logged in'}
def CreateFriendRequest(request):
    if(request.user.is_authenticated):
        if(FriendRequestCode.objects.filter(user=request.user).exists()):
            FriendRequestCode.objects.get(user=request.user).delete()
        request = FriendRequestCode.objects.create(user=request.user)
        request.save()
        return JsonResponse({'code':request.code})
    return {'message': 'user not logged in'}
def GetFriendChatId(request,pk):
    if(request.user.is_authenticated):
        try:
            user = CustomUser.objects.get(id=pk)
        except ObjectDoesNotExist:
            return {'message': "friend doesn't exist"}
        try:
            chat=FriendChat.objects.filter(users=user).get(users=request.user)
        except ObjectDoesNotExist:
            return {'message': "friendchat doesn't exist"}
        return JsonResponse({"id":chat.id})
    return {'message': 'user not logged in'}
def GetGroupChatId(request,pk):
    if(request.user.is_authenticated):
        try:
            invite=GroupInviteCode.objects.get(id=pk)
        except ObjectDoesNotExist:
            try:
                invite=GroupInvitePrivate.objects.get(id=pk)
            except ObjectDoesNotExist:
                return {'message': "groupchat doesn't exist"}
        return {"id":invite.group.id}
    return {'message': 'user not logged in'}
class MessageView(View):
    def get(self, request):
        messages = Message.objects.all()
        return render(request, 'messages.html', {'messages': messages})

    def post(self, request):
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('messages')
        return render(request, 'message_form.html', {'form': form})

    def delete(self, request):
        Message.objects.all().delete()
        return redirect('messages')

class FriendRequestDeleteView(View):
    def delete(self, request):
        FriendRequestPrivate.objects.all().delete()
        FriendRequestCode.objects.all().delete()
        return redirect('auth')

class FriendChatDeleteView(View):
    def delete(self,request):
        FriendChat.objects.all().delete()
        return redirect('auth')
class GroupChatDeleteView(View):
    def delete(self,request):
        GroupChat.objects.all().delete()
        return redirect('auth')
class MessageDeleteView(View):
    def delete(self,request):
        Message.objects.all().delete()
        return redirect('auth')
class GroupInvitePrivateDeleteView(View):
    def delete(self,request):
        GroupInvitePrivate.objects.all().delete()
        return redirect('auth')
class GroupInviteCodeDeleteView(View):
    def delete(self,request):
        GroupInviteCode.objects.all().delete()
        return redirect('auth')
class GroupChatCreateView(View):
    def get(self,request):
        if(request.user.is_authenticated):
            create_form = GroupChatCreate()
            return render(request, 'group.html', {'group_create_form': create_form})
    def post(self,request):
        create_form = GroupChatCreate()
        if create_form.is_valid():
            group = GroupChat.objects.create(name=create_form.cleaned_data['group_name'],host=request.user,last_name=create_form.cleaned_data['group_name'])
            group.users.add(request.user)
            group.users.add(CustomUser.objects.get(username="server"))
            group.save()
            return redirect(f'chat/g/{group.id}')
class UserAuthView(View):
    def get(self, request):
        register_form = UserRegistrationForm()
        login_form = UserLoginForm()
        return render(request, 'auth.html', {'register_form': register_form, 'login_form': login_form})

    def post(self, request):
        if 'register' in request.POST:
            register_form = UserRegistrationForm(request.POST)
            login_form = UserLoginForm()
            if register_form.is_valid():
                user = CustomUser.objects.create_user(username=register_form.cleaned_data['username'], password=register_form.cleaned_data['password'])
                print(user)
                login(request, user)    
        elif 'login' in request.POST:
            login_form = UserLoginForm(request.POST)
            register_form = UserRegistrationForm()
            if login_form.is_valid():
                username = login_form.cleaned_data['username']
                if(username != "server"):
                    password = login_form.cleaned_data['password']
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        print(user.id)
                        login(request, user)
                    else:
                        login_form.add_error(None, "Invalid credentials provided")
                else:
                    login_form.add_error(None, "Cannot login as server")
        return render(request, 'auth.html', {'register_form': register_form, 'login_form': login_form})
class UserLogoutView(View):
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect('auth')
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect('auth')
def get_friend_by_code(request,pk):
    if(request.user.is_authenticated):
        try:
            request = FriendRequestCode.objects.get(code=pk,available=False)
        except ObjectDoesNotExist:
            return {"balbalbahjabl"}
        chat_id = FriendChat.objects.filter(users=request.user).get(users=request.user).id
        request_id = request.user.id
        request_username = request.user.username
        request.delete()
        return JsonResponse({"chat_id": chat_id,"id":request_id,"username":request_username})
def FriendAdd(request):
    if request.method == 'POST':
        form = FriendChatAdd(request.POST)
        if(form.is_valid()):
            if(request.user.is_authenticated):
                second_p = CustomUser.objects.get(id=form.cleaned_data['friend'])
                type = form.cleaned_data['type']
                if type=='Delete' and FriendChat.objects.filter(users=request.user).filter(users=second_p).exists():
                    FriendChat.objects.filter(users=request.user).filter(users=second_p).delete()
                elif type == 'Delete':
                    form.add_error(None, "Users aren't friends!")
                elif FriendChat.objects.filter(users=request.user).filter(users=second_p).exists():
                    form.add_error(None, "User is already friends with this person.")
                else:
                    chat = FriendChat.objects.create()
                    chat.users.add(request.user)
                    chat.users.add(second_p)
                    chat.save()
                    return render(request, 'friend.html', {'add_friend_form': add_friend_form})
            else:
                return redirect('/auth/')
    else:
        add_friend_form = FriendChatAdd()
        return render(request, 'friend.html', {'add_friend_form': add_friend_form})
# class ChatView(View):
#     def post(self, request, pk):
#         chat, created = Chat.objects.get_or_create(id=pk)
#         if request.user not in chat.users.all():
#             chat.users.add(request.user)
#             chat.save()
#         return redirect('chat', pk=pk)


def set_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

