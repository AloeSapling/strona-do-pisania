import json
from django.core.serializers import serialize
from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from backend_app.models import FriendChat,FriendRequestPrivate,FriendRequestCode,CustomUser,Message,GroupChat, GroupInviteCode, GroupInvitePrivate,BanList
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone






def serialize_with_id(objects):
    data = serialize('json', objects)
    deserialized_data = json.loads(data)
    for item in deserialized_data:
        fields = item['fields']
        fields['id'] = item['pk']
    return json.dumps(deserialized_data[0]['fields'], cls=DjangoJSONEncoder)

async def async_serialize_with_id(objects):
    data = await sync_to_async(serialize)('json', objects)
    deserialized_data = json.loads(data)
    for item in deserialized_data:
        fields = item['fields']
        fields['id'] = item['pk']
    return json.dumps(deserialized_data[0]['fields'], cls=DjangoJSONEncoder)
def serialize_multiple_with_id(objects):
    data = serialize('json', objects)
    deserialized_data = json.loads(data)
    for item in deserialized_data:
        fields = item['fields']
        fields['id'] = item['pk']
    print([x.fields for x in deserialized_data])
    return json.dumps([x.fields for x in deserialized_data], cls=DjangoJSONEncoder)










@database_sync_to_async
def create_friend_request(to_user_id, curr_user):
    if(CustomUser.objects.filter(id=to_user_id).exists() == False):
        return {'status': '400', 'message':'user does not exist'}
    user = CustomUser.objects.get(id=to_user_id)
    if(FriendChat.objects.filter(users=curr_user).filter(users=user).exists()):
        return {'status': '400', 'message':'users are already friends'}
    if(FriendRequestPrivate.objects.filter(from_user=curr_user,to_user=user, available=True).exists()):
        return {'status': '400', 'message': 'request already sent between the two users'}
    FriendRequestPrivate.objects.create(from_user=curr_user,to_user=user)
    user_data = json.loads(serialize_with_id([user]))
    return {'status': '200','message':'request created successfully','user':user_data}
@database_sync_to_async
def accept_friend_request(type,identifier,curr_user):
    #identifier should be id of the from_user if the request is of type private or the friend request code if the request is of type code
    if(type=="private"):
        if(CustomUser.objects.filter(id=identifier).exists() == False):
            return {'status': '400', 'message':'user does not exist'}
        user = CustomUser.objects.get(id=identifier)
        if(FriendRequestPrivate.objects.filter(from_user=user,to_user=curr_user,available=True).exists()==False):
            return {'status': '400', 'message': 'friend request between the two users does not exist or is unavailable'}
        if(FriendChat.objects.filter(users=curr_user).filter(users=user).exists()):
            return {'status': '400', 'message':'users are already friends'}
        request = FriendRequestPrivate.objects.get(from_user=user,to_user=curr_user,available=True)
        request.delete()
        new_chat = FriendChat.objects.create()
        chat_id = new_chat.id
        new_chat.users.add(curr_user)
        new_chat.users.add(user)
        new_chat.save()
        user_data = json.loads(serialize_with_id([user]))
        return {'status': '200','message':'request accepted successfully', 'user':user_data, 'friend_id': chat_id}
    elif type =="code":
        if(FriendRequestCode.objects.filter(code=identifier,available=True).exists() == False):
            return {'status': '400', 'message':'friend request with given code does not exist or is unavailable'}
        friend_request = FriendRequestCode.objects.get(code=identifier,available=True)
        if(FriendChat.objects.filter(users=curr_user).filter(users=friend_request.user).exists()):
            return {'status': '400', 'message':'users are already friends'}
        rem = False
        user = friend_request.user
        if(FriendRequestPrivate.objects.filter(from_user=friend_request.user,to_user=curr_user,available=True).exists()):
            request = FriendRequestPrivate.objects.get(from_user=friend_request.user,to_user=curr_user,available=True)
            request.delete()
            rem = True
        friend_request.delete()
        new_chat = FriendChat.objects.create()
        chat_id = new_chat.id
        new_chat.users.add(curr_user)
        new_chat.users.add(friend_request.user)
        new_chat.save()
        user_data = json.loads(serialize_with_id([user]))
        return {'status': '200','message':'request accepted successfully', 'user':user_data, 'removed_existing': rem, 'friend_id': chat_id}
    return {'status': '400','message':'bad friend request type provided'}
@database_sync_to_async
def reject_friend_request(from_user_id, curr_user):
    if(CustomUser.objects.filter(id=from_user_id).exists() == False):
        return {'status': '400', 'message':'user does not exist'}
    user = CustomUser.objects.get(id=from_user_id)
    if(FriendRequestPrivate.objects.filter(from_user=user,to_user=curr_user,available=True).exists()==False):
        return {'status': '400', 'message': 'friend request between the two users does not exist or is already unavailable'}
    request = FriendRequestPrivate.objects.get(from_user=user,to_user=curr_user,available=True)
    request.delete()
    user_data = json.loads(serialize_with_id([user]))
    return {'status': '200', 'message': 'friend request rejected successfully', 'user': user_data}
@database_sync_to_async
def remove_friend(friend_id,curr_user):
    if(CustomUser.objects.filter(id=friend_id).exists()==False):
        return {'status': '400', 'message':'user does not exist'}
    user = CustomUser.objects.get(id=friend_id)
    if(FriendChat.objects.filter(users=curr_user).filter(users=user).exists() == False):
        return {'status': '400', 'message':'users are not friends'}
    chat = FriendChat.objects.filter(users=curr_user).get(users=user)
    chat_id = chat.id
    chat.delete()
    user_data = json.loads(serialize_with_id([user]))
    return {'status':'200','message': 'friend removed successfully', 'user': user_data, 'friend_id': chat_id}





@database_sync_to_async
def check_if_in_friend_chat(curr_user,id):
    if(FriendChat.objects.filter(id=id,users=curr_user).exists()):
        return True
    return False
@database_sync_to_async
def add_message_to_friend_chat(message,curr_user,id):
    if(FriendChat.objects.filter(id=id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat = FriendChat.objects.get(id=id)
    mess = Message.objects.create(content=message,author=curr_user)
    chat.messages.add(mess)
    return {'status': '200','message': 'message added successfully', "message_obj": json.loads(serialize_with_id([mess])),'date_of_creation': chat.date_of_creation.isoformat()}
@database_sync_to_async
def edit_friend_chat_message(message_id,curr_user,new_message,id):
    if(FriendChat.objects.filter(id=id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat = FriendChat.objects.get(id=id)
    if(chat.messages.filter(id=message_id).exists() == False):
        return {'status': '400', 'message': 'given message does not exist in chat'}
    mess = FriendChat.messages.get(id=message_id)
    if(mess.author.id != curr_user.id):
        return {'status': '403', 'message': 'user is not author of message'}
    mess.content = new_message
    mess.edited = True
    mess.save()
    return {'status': '200', 'message': 'message edited successfully', 'message': json.loads(serialize_with_id([mess]))}
@database_sync_to_async
def delete_friend_chat_message(message_id,curr_user,id):
    if(FriendChat.objects.filter(id=id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat = FriendChat.objects.get(id=id)
    if(chat.messages.filter(id=message_id).exists() == False):
        return {'status': '400', 'message': 'given message does not exist in chat'}
    mess = FriendChat.messages.get(id=message_id)
    if(mess.author.id != curr_user.id):
        return {'status': '403', 'message': 'user is not author of message'}
    mess_data = mess
    mess.delete()
    return {'status': '200', 'message': 'message edited successfully', 'message': json.loads(serialize_with_id([mess_data]))}












@database_sync_to_async
def check_if_in_group_chat(curr_user,id):
    if(GroupChat.objects.filter(id=id,users=curr_user).exists()):
        return True
    return False
@database_sync_to_async
def check_if_new_in_group_chat(curr_user,id):
    chat = GroupChat.objects.get(id=id)
    if(chat.new_users.filter(id=curr_user.id).exists()):
        chat.new_users.remove(id=curr_user.id)
        return True
    return False
@database_sync_to_async
def get_server_user():
    return CustomUser.objects.get(username="server")
@database_sync_to_async
def add_message_to_group_chat(message,curr_user,id):
    if(GroupChat.objects.filter(id=id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat = GroupChat.objects.get(id=id)
    mess = Message.objects.create(content=message,author=curr_user)
    chat.messages.add(mess)
    return {'status': '200','message': 'message added successfully',"message_obj": json.loads(serialize_with_id([mess])), 'date_of_creation': chat.date_of_creation.isoformat()}


@database_sync_to_async
def edit_group_message(message_id,group_id,curr_user,new_message):
    if(GroupChat.objects.filter(id=group_id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.messages.filter(id-message_id).exist() == False):
        return {'status': '400', 'message': 'given message does not exist in chat'}
    message = chat.messages.get(id=message_id)
    if(message.author.id != curr_user.id):
        return {'status': '403', "message": "user is not author of given message"}
    message.content = new_message
    message.edited = True
    message.save()
    return {'status': '200','message': 'message edited sucessfully', 'message_obj': json.loads(serialize_with_id([message]))}
@database_sync_to_async
def delete_group_message(message_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists() == False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.messages.filter(id-message_id).exist() == False):
        return {'status': '400', 'message': 'given message does not exist in chat'}
    message = chat.messages.get(id=message_id)
    if(message.author.id != curr_user.id):
        return {'status': '403', "message": "user is not author of given message"}
    message_data = message
    message.delete()
    return {'status': '200','message': 'message deleted sucessfully', 'message_obj': json.loads(serialize_with_id([message_data]))}
@database_sync_to_async
def kick_group_user(user_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.host.id != curr_user.id):
        return {"status": '403', "message": 'user not group host'}
    if(chat.users.filter(id=user_id).exists() == False):
        return {'status': '400', "message": 'user not in group'}
    user = CustomUser.objects.get(id=user_id)
    chat.users.remove(id=user.id)
    chat.users.save()
    return {'status': '200', 'message': 'user kicked successfully', 'user': json.loads(serialize_with_id([user]))}
@database_sync_to_async
def ban_group_user(user_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.host.id != curr_user.id):
        return {"status": '403', "message": 'user not group host'}
    if(chat.users.filter(id=user_id).exists() == False):
        return {'status': '400', "message": 'user not in group'}
    user = CustomUser.objects.get(id=user_id)
    if(BanList.objects.filter(user__id=user.id).exists()):
        return {'status': '400', "message": 'user already banned'}
    chat.users.remove(id=user.id)
    chat.users.save()
    BanList.objects.create(group=chat,user=user)
    return {'status': '200', 'message': 'user banned successfully', 'user': json.loads(serialize_with_id([user]))}
@database_sync_to_async
def unban_group_user(user_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.host.id != curr_user.id):
        return {"status": '403', "message": 'user not group host'}
    if(CustomUser.objects.filter(id=user_id) == False):
        return {'status': '400', "message": "user of given id does not exist"}
    user = CustomUser.objects.get(id=user_id)
    if(BanList.objects.filter(user__id=user.id).exists() == False):
        return {'status': '400', "message": 'user is not already banned'}
    BanList.objects.get(group=chat,user=user).delete()
    return {'status': '200', 'message': 'user unbanned successfully', 'user': json.loads(serialize_with_id([user]))}
@database_sync_to_async
def change_group_name(name,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.host.id != curr_user.id):
        return {"status": '403', "message": 'user not group host'}
    if(chat.name == name):
        return {'status': '400', 'message': 'this is already the group name'}
    chat.last_name = chat.name
    chat.name = name
    chat.save()
    return{'status': '200', 'message': 'group name changed successfully', 'group': json.loads(serialize_with_id([chat]))}
@database_sync_to_async
def change_group_host(new_host_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.host.id != curr_user.id):
        return {"status": '403', "message": 'user not group host'}
    if(CustomUser.objects.filter(id=new_host_id).exists() == False):
        return {'status': '400', 'message': 'user of given id does not exist'}
    user = CustomUser.objects.get(id=new_host_id)
    if(chat.users.filter(id=user.id).exists() == False):
        return {'status': '400', 'message': 'user of given id does not exist in chat'}
    if(chat.host.id == new_host_id):
        return {'status': '400', 'message': 'user is already group host'}
    chat.host = user
    chat.save()
    return {'status': '200', 'message': 'host changed successfully', 'group': json.loads(serialize_with_id([chat]))}
@database_sync_to_async
def leave_group(group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists()==False):
        return {'status': '400', 'message': 'given chat does not exist'}
    chat  = GroupChat.objects.get(id=group_id)
    if(chat.users.filter(id=curr_user.id).exists() == False):
        return{'status': '400', 'message': 'user not within group'}
    chat.users.remove(curr_user)
    chat_data = chat
    deleted = False
    if(curr_user.id == chat.host.id):
        chat.delete()
        deleted = True
    return {'status': '200', 'message': 'left group successfully', 'group': json.loads(serialize_with_id([chat_data])), 'deleted': deleted}



@database_sync_to_async
def create_group_invite_private(group_id,curr_user,to_user_id):
    if(GroupChat.objects.filter(id=group_id).exists() == False):
        return {'status': '400', 'message': 'group of given id does not exist'}
    if(CustomUser.objects.filter(id=to_user_id).exists()==False):
        return {'status': '400', 'message': 'user of given id does not exist'}
    group = GroupChat.objects.get(id=group_id)
    if(group.users.filter(id=to_user_id).exists()):
        return {'status': '400', 'message': 'user you are trying to invite is already within group'}
    if(group.users.filter(id=curr_user.id).exists() == False):
        return {'status': '403', 'message': 'user is not within group'}
    user = CustomUser.objects.get(id=to_user_id)
    if(BanList.objects.filter(group=group,user=user).exists()):
        return {'status': '400', 'message': 'user you are trying to invite is banned from the group'}
    invite = GroupInvitePrivate.objects.create(group=group,to_user = user,from_user=curr_user)
    return {'status': '200', 'message': 'invite created successfully', 'group': json.loads(serialize_with_id([group])), 'group_invite_id': invite.id, 'user':json.loads(serialize_with_id([user]))}
@database_sync_to_async
def accept_group_invite(request_type,identifier,curr_user):
    #identifier should be id of the invite if the request is of type private or the group invite code if the request is of type code
    if(request_type == "private"):
        if(GroupInvitePrivate.objects.filter(id=identifier).exists() == False):
            return {'status': '400', 'message': 'group invite of given id does not exist'}
        invite = GroupInvitePrivate.objects.get(id=identifier)
        if(invite.to_user.id != curr_user.id):
            return {'status': '400', 'message': 'group invite of given id was not meant for you'}
        invite_id = invite.id
        user = json.loads(serialize_with_id([invite.from_user]))
        group = GroupChat.objects.get(id=invite.group.id)
        if(BanList.objects.filter(group=group,user=curr_user).exists()):
            return {'status': '403', 'message': 'you are banned from the group'}
        if(group.users.filter(id=curr_user.id).exists()):
            return {'status': '400', 'message': 'user already within group'}
        group_data = json.loads(serialize_with_id([group]))
        group.users.add(curr_user)
        group.save()
        invite.delete()
        return {'status': '200', 'message': 'accepted invite successfully', 'user': user, 'group':group_data,'group_invite_id':invite_id}
    elif(request_type == "code"):
        if(GroupInviteCode.objects.filter(code=identifier).exists() == False):
            return {'status': '400', 'message': 'group invite with given code does not exist'}
        invite = GroupInviteCode.objects.get(code=identifier)
        if(GroupChat.objects.filter(id=invite.group.id).exists() == False):
            return {'status': '400', 'message': 'group does not exist'}
        invite_id = ''
        toremove = False
        user = {}
        if(GroupInvitePrivate.objects.filter(group=invite.group,to_user=curr_user).exists()):
            private_invite = GroupInvitePrivate.objects.get(group=invite.group,to_user=curr_user)
            user = json.loads(serialize_with_id([private_invite.from_user]))
            invite_id = private_invite.id
            private_invite.delete()
            toremove =True

        group = GroupChat.objects.get(id=invite.group.id)
        if(BanList.objects.filter(group=group,user=curr_user).exists()):
            return {'status': '403', 'message': 'you are banned from the group'}
        if(group.users.filter(id=curr_user.id).exists()):
            return {'status': '400', 'message': 'user already within group'}
        group.users.add(curr_user)
        return {'status': '200', 'message': 'group invite accepted successfully', 'removed_existing': toremove, 'user': user, 'group_invite_id': invite_id, 'group': json.loads(serialize_with_id([group]))}
    else:
        return {'status': '400', 'message': 'bad request type provided'}
@database_sync_to_async    
def reject_group_invite(group_invite_id,curr_user):
    if(GroupInvitePrivate.objects.filter(id=group_invite_id).exists() ==False):
        return {'status': '400', 'message': 'group invite of given id does not exist'}
    invite = GroupInvitePrivate.objects.get(id=group_invite_id)
    if(invite.to_user.id != curr_user.id):
        return {'status': '400', 'message': 'group invite of given id was not meant for you'}
    group = GroupChat.objects.get(id=invite.group.id)
    if(group.users.filter(id=curr_user.id).exists()):
        return {'status': '400', 'message': 'user already within group'}
    invite_id = invite.id
    user = json.loads(serialize_with_id(invite.from_user))
    invite.delete()
    return {'status': '200', 'message': 'invite rejected successfully', 'user': user, 'group': json.loads(serialize_with_id([group])), 'group_invite_id': invite_id}
@database_sync_to_async
def verify_group_host(host,group_id):
    if(GroupChat.objects.filter(id=group_id).exists() == False):
        return {'status': '400', 'message': 'group chat of given id does not exist'}
    group = GroupChat.objects.get(id=group_id)
    if(group.host.id != host.id):
        return {'status': '403', 'message': 'user is not host of given group'}
    return {'status': '200', 'message':'user is host of group','group':json.loads(serialize_with_id([group]))}
@database_sync_to_async
def get_group_members(group_id):
    if(GroupChat.objects.filter(id=group_id).exists() == False):
        return {'status': '400', 'message': 'group chat of given id does not exist'}
    chat = GroupChat.objects.get(id=group_id)
    members = chat.users
    return {'status': '200', 'message': 'users got successfully', 'users': json.loads(serialize_multiple_with_id(members))}
@database_sync_to_async
def verify_group_host_by_id(host_id,group_id,curr_user):
    if(GroupChat.objects.filter(id=group_id).exists() == False):    
        return {'status': '400', 'message': 'group chat of given id does not exist'}
    group = GroupChat.objects.get(id=group_id)
    if(CustomUser.objects.filter(id=host_id).exists() == False):
        return {'status': '400', 'message': 'group chat of given id does not exist'}
    if(group.host.id != host_id and curr_user.id != group.host.id):
        return {'status': '403', 'message': 'user is not host of given group'}
    user = CustomUser.objects.get(id=host_id)
    return {'status': '200', 'message': 'one of users is host', 'user': json.loads(serialize_with_id([user]))}












class FriendChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope["user"]
        if self.user.is_authenticated and await check_if_in_friend_chat(self.user,self.room_name):
            self.room_group_name = f"friend_chat_{self.room_name}"
            print(self.room_group_name)
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )
            print(self.room_group_name)
            await self.accept()
        else:
            await self.close()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
    async def receive(self, text_data):
        if (await check_if_in_friend_chat(self.user,self.room_name)):
            text_data_json = json.loads(text_data)
            if(text_data_json['action']):
                action = text_data_json['action']
                if(action == "send_message"):
                    if(text_data_json["message"]):
                        message = text_data_json["message"]
                        res = await add_message_to_friend_chat(message,self.user,self.room_name)
                        if res['status'] == '200':
                            date_of_creation = res['date_of_creation']
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_sent", "data":
                                                       {
                                                        "message": res['message_obj'], 
                                                        "author": json.loads(await async_serialize_with_id([self.user])), 
                                                        "date_of_creation": date_of_creation
                                                        }}
                            )
                    else:
                        return {'status': '400', 'message': 'no message provided in request'}
                elif(action == "edit_message"):
                    if(text_data_json["message_id"] and text_data_json["new_message"]):
                        message_id = text_data_json["message_id"]
                        new_message = text_data_json["new_message"]
                        res = await edit_friend_chat_message(message_id,self.user,self.room_name,new_message)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_edited", "data":
                                                       { 
                                                        "message": res['message']
                                                        }}
                            )
                    else:
                        return {'status': '400', 'message': 'no message id provided or no new message provided in request'}
                elif(action == "delete_message"):
                    if(text_data_json["message_id"]):
                        message_id = text_data_json["message_id"]
                        res = await delete_friend_chat_message(message_id,self.user,self.room_name)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_deleted", "data":
                                                       { 
                                                        "message": res['message']
                                                        }}
                            )
                    else:
                        return {'status': '400', 'message': 'no message id provided'}
            else:
                return {'status': '400', 'message': 'no action provided in request'}
        else:
            await self.close()
    async def send_notification(self, event):
        message = event["message"]
        data = event["data"]
        print("testing")
        await self.send(text_data=json.dumps({"message": message, "data": data}))
















class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope["user"]
        if self.user.is_authenticated and await check_if_in_group_chat(self.user,self.room_name):
            self.room_group_name = f"group_chat_{self.room_name}"
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )
            await self.accept()
            if(check_if_new_in_group_chat(self.scope['user'],self.room_name)):
                author = json.loads(await async_serialize_with_id(get_server_user()))
                await add_message_to_group_chat(f"{self.scope['user']['username']} has joined the group chat",author,self.room_name)
                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'chat_message', "message": f"{self.scope['user']['username']} has joined the group chat", "author": author, "date_of_creation": timezone.now()}
                )
                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'send_notification', "message": "user_joined", "data": {
                        "user": json.loads(await async_serialize_with_id(self.scope['user']))
                    }}
                )
        else:
            await self.close()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
    async def receive(self, text_data):
        if(await check_if_in_group_chat(self.user,self.room_name)):
            text_data_json = json.loads(text_data)
            if(text_data_json['action']):
                action = text_data_json['action']
                if(check_if_new_in_group_chat(self.scope['user'],self.room_name)):
                    author = json.loads(await async_serialize_with_id(get_server_user()))
                    await add_message_to_group_chat(f"{self.scope['user']['username']} has joined the group chat",author,self.room_name)
                    await self.channel_layer.group_send(
                        self.room_group_name, {'type': 'chat_message', "message": f"{self.scope['user']['username']} has joined the group chat", "author": author, "date_of_creation": timezone.now()}
                    )
                    await self.channel_layer.group_send(
                        self.room_group_name, {'type': 'send_notification', "message": "user_joined", "data": {
                            "user": json.loads(await async_serialize_with_id(self.scope['user']))
                        }}
                    )
                if(action == "send_message"):
                    if(text_data_json["message"]):
                        message = text_data_json["message"]
                        res = await add_message_to_group_chat(message,self.user,self.room_name)
                        if res['status'] == '200':
                            date_of_creation = res['date_of_creation']
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_sent", 
                                                       "data":{
                                                           "message": res['message_obj'],
                                                            "author": json.loads(await async_serialize_with_id([self.user])), 
                                                            "date_of_creation": date_of_creation
                                                            }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no message provided in request'}
                elif(action == "edit_message"):
                    if(text_data_json["message_id"]):
                        message_id = text_data_json["message_id"]
                        res = await edit_group_message(message_id,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_edited", 
                                                       "data":{
                                                           "message": res['message_obj'],
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no message id provided in request'}
                elif(action == "delete_message"):
                    if(text_data_json["message_id"]):
                        message_id = text_data_json["message_id"]
                        res = await delete_group_message(message_id,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "message_deleted", 
                                                       "data":{
                                                           "message": res['message_obj'],
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no message id provided in request'}
                elif(action == "kick_user"):
                    if(text_data_json["user_id"]):
                        user_id = text_data_json['user_id']
                        res= await kick_group_user(user_id,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "user_kicked", 
                                                       "data":{
                                                           "user": res['user'],
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no user id provided in request'}
                elif(action == "ban_user"):
                    if(text_data_json["user_id"]):
                        user_id = text_data_json['user_id']
                        res= await ban_group_user(user_id,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "user_banned", 
                                                       "data":{
                                                           "user": res['user'],
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no user id provided in request'}
                elif(action == "unban_user"):
                    if(text_data_json["user_id"]):
                        user_id = text_data_json['user_id']
                        res= await unban_group_user(user_id,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "user_unbanned", 
                                                       "data":{
                                                           "user": res['user'],
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no user id provided in request'}
                elif(action == "change_name"):
                    if(text_data_json["new_name"]):
                        new_name = text_data_json['new_name']
                        res= await change_group_name(new_name,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "group_name_changed", 
                                                       "data":{
                                                            "new_name": new_name
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no new group name provided in request'}
                elif(action == "change_host"):
                    if(text_data_json["new_host"]):
                        new_host = text_data_json['new_host']
                        res= await change_group_host(new_host,self.room_name,self.user)
                        if res['status'] == '200':
                            await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "group_host_changed", 
                                                       "data":{
                                                            "new_name": new_host
                                                       }
                                    }
                            )
                    else:
                        return {'status': '400', 'message': 'no new group host provided in request'}
                elif(action == "leave_group"):
                    res = await leave_group(self.room_name,self.user)
                    if(res['status'] == '200' and res['deleted'] == False):
                        await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_notification", "message": "user_left", 
                                                       "data":{
                                                            "user": json.loads(serialize_with_id([self.user]))
                                                       }
                                    }
                            )
                    elif(res['status']=='200' and res['deleted']):
                        await self.channel_layer.group_send(
                                self.room_group_name, {"type": "send_group_disband", "message": "group_disbanded", 
                                    }
                            )
            else:
                return {'status': '400', 'message': 'no action provided in request'}
        else:
            await self.close()
    async def send_notification(self,event):
        message = event['message']
        data = event['data']
        await self.send(text_data=json.dumps({"message": message, "data": data}))
    async def send_group_disband(self,event):
        message = event['message']
        await self.send(text_data=json.dumps({"message":message}))
        await self.close()








        
class CommunicateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            print("connect",self.group_name)
            print(self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        if(data.get('action')):
            action = data.get('action')
            print("recieve",action)
            if action == 'send_friend_request':
                if(data.get('to_user_id')):
                    to_user_id = data.get('to_user_id')
                    print("test1")
                    res = await create_friend_request(to_user_id,self.user)
                    print("test2")
                    if res['status'] == '200':
                        print("test3")
                        await self.channel_layer.group_send(
                        f"user_{to_user_id}",
                        {
                            'type': 'send_notification',
                            'message': "friend_request_recieved",
                            "data": {
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                        },
                        }
                        )
                        print("test4")
                else:
                    return {'status': '400', 'message': 'no to_user_id provided'}
            elif action == 'accept_friend_request':
                identifier = ""
                if(data.get('type')):
                    request_type = data.get('type')
                    if(request_type=="private"):
                        if(data.get('from_user_id')):
                            identifier = data.get('from_user_id')
                        else:
                            return {'status': '400', 'message': 'no from_user id provided provided'}
                    if(request_type=="code"):
                        if(data.get('code')):
                            identifier = data.get('code')
                        else:
                            {'status': '400', 'message': 'no friend request code provided provided'}
                    res = await accept_friend_request(request_type,identifier,self.user)
                    toremove = False
                    if (request_type=="private" or (request_type=="code" and res['removed_existing'] == True)):
                        toremove = True
                    if(res['status'] == '200'):
                        await self.notify(res['user']['id'],"friend_request_accepted",
                                    data={
                                        "from_user":json.loads(await async_serialize_with_id([self.user])),
                                        "should_remove":toremove,
                                        "friend_id": res['friend_id'],
                                        })
                else:
                    return {'status': '400', 'message': 'no request type provided'}
            elif action == 'reject_friend_request':
                if(data.get('from_user_id')):
                    from_user_id = data.get('from_user_id')
                    res = await reject_friend_request(from_user_id,self.user)
                    if res['status'] == '200':
                        await self.notify(res['user']['id'],"friend_request_rejected",
                                    data={
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                        })
                else:
                    return {'status': '400', 'message': 'no from_user_id provided'}
            elif action == 'remove_friend':
                if(data.get('friend_id')):
                    friend_id = data.get("friend_id")
                    res= await remove_friend(friend_id,self.user)
                    if res['status'] == '200':
                        await self.notify(friend_id,"friend_removed",
                                    data={
                                        "from_user":json.loads(await async_serialize_with_id([self.user])),
                                        'friend_id': friend_id
                                        })
                        
                else:
                    return {'status': '400', 'message': 'no friend id provided'}












            elif action == "send_group_invite":
                if(data.get('group_id') and data.get('to_user_id')):
                    group_id = data.get('group_id')
                    to_user_id = data.get('to_user_id')
                    res = await create_group_invite_private(group_id,self.user,to_user_id)
                    if res['status'] == '200':
                        await self.notify(to_user_id,"group_invite_recieved",
                                    data={
                                        "group":res['group'],
                                        "group_invite_id": res['group_invite_id'],
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                        })
                    else:
                        return {'status': '400', 'message': 'no to_user_id provided or no group id provided'}
            elif action == "accept_group_invite":
                identifier = ""
                if(data.get('type')):
                    invite_type = data.get('type')
                    if(invite_type=="private"):
                        if(data.get('group_invite_id')):
                            identifier = data.get('group_invite_id')
                        else:
                            return {'status': '400', 'message': 'no invite id provided provided'}
                    if(invite_type=="code"):
                        if(data.get('code')):
                            identifier = data.get('code')
                        else:
                            {'status': '400', 'message': 'no invite code provided provided'}
                    res = await accept_group_invite(invite_type,identifier,self.user)
                    if(res['status'] == '200' and (invite_type=="private" or (invite_type=="code" and res['removed_existing'] == True))):
                        await self.notify(res['user'].id,"group_invite_accepted",
                                    data={
                                        'group':res['group'],
                                        'group_invite_id':res['group_invite_id']
                                        })
                else:
                    return {'status': '400', 'message': 'no invite type provided provided'}
            elif action == "reject_group_invite":
                if(data.get('group_invite_id')):
                    group_invite_id = data.get('group_invite_id')
                    res = await reject_group_invite(group_invite_id,self.user)
                    if res['status'] == '200':
                        await self.notify(res['user'].id,"group_invite_rejected",
                                    data={
                                        "group":res['group'],
                                        "group_invite_id":group_invite_id
                                        })
                else:
                    return {'status': '400', 'message': 'no invite id provided provided'}
            elif action == "kick_group_member":
                if(data.get('group_id') and data.get('member_id')):
                    group_id = data.get('group_id')
                    member_id = data.get('member_id')
                    res = await verify_group_host(self.user,group_id)
                    if res['status'] == '200':
                        await self.notify(member_id,"kicked_from_group",
                                    data={
                                        "group":res['group'],
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                        })
                else:
                    return {'status': '400', 'message':'no group id provided or no member id provided'}
            elif action == "ban_group_member":
                if(data.get('group_id') and data.get('member_id')):
                    group_id = data.get('group_id')
                    member_id = data.get('member_id')
                    res = await verify_group_host(self.user,group_id)
                    if res['status'] == '200':
                        await self.notify(member_id,"banned_from_group",
                                    data={
                                        "group":res['group'],
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                    })
                else:
                    return {'status': '400', 'message':'no group id provided or no member id provided'}
            elif action == "unban_group_member":
                if(data.get('group_id') and data.get('member_id')):
                    group_id = data.get('group_id')
                    member_id = data.get('member_id')
                    res = await verify_group_host(self.user,group_id)
                    if res['status'] == '200':
                        await self.notify(member_id,"unbanned_from_group",
                                    data={
                                        "group":res['group'],
                                        "from_user":json.loads(await async_serialize_with_id([self.user]))
                                    })
                else:
                    return {'status': '400', 'message':'no group id provided or no member id provided'}
            elif action == "group_name_change":
                if(data.get('group_id') and data.get('changed_group_name') and data.get("old_group_name")):
                    group_id = data.get('group_id')
                    changed_name =  data.get('changed_group_name')
                    old_name = data.get("old_group_name")
                    res = await get_group_members(group_id)
                    if res['status'] == '200':
                        await self.notify_multiple(res['user_ids'],"group_name_changed",
                                            data={
                                                "previous_group_name": old_name,
                                                "changed_name": changed_name,
                                                "group": res['group'],
                                                "from_user":json.loads(await async_serialize_with_id([self.user]))
                                            })
                else:
                    return {'status': '400', 'message': 'no group id provided or no changed group name provided or no old group name provided'}
            elif action == "group_host_change":
                if(data.get('group_id') and data.get('group_host_id')):
                    group_id = data.get('group_id')
                    group_host_id = data.get('group_host_id')
                    res2 = await verify_group_host_by_id(group_host_id,group_id)
                    if( res2['status'] == '200'):
                        res = await get_group_members(group_id)
                        if res['status'] == '200':
                            await self.notify_multiple(res['user_ids'],"group_host_changed",
                                                       data={
                                                           "new_host": res2['group_host'],
                                                           "group": res['group'],
                                                           "from_user": json.loads(await async_serialize_with_id([self.user]))
                                                       })
                    else:
                        return {'status': '403', 'message': 'not group host'}
                else:
                    return {'status': '400', 'message': 'no group id provided or no group host provided'}
            elif action == "group_delete":
                if(data.get('group_id') and data.get('member_ids')):
                    group_id = data.get('group_id')
                    member_ids = data.get('member_ids')
                    await self.notify_multiple(member_ids,"group_deleted",
                                               data={
                                                   "group_id": group_id,
                                                   "from_user": json.loads(await async_serialize_with_id([self.user]))
                                               })
                else:
                    return {'status': '400', 'message': 'no group id provided or no member ids provided'}
        else:
            return {'status': '400', 'message': 'no action provided'}












    async def notify(self,to_user_id,message,data):
        await self.channel_layer.group_send(
            f"user_{to_user_id}",
            {
                'type':'send_notification',
                'message': message,
                "data": data,
            }
        )
    async def notify_multiple(self,to_user_ids,message,data):
        for to_user_id in to_user_ids:
            await self.channel_layer.group_send(
            f"user_{to_user_id}",
            {
                'type':'send_notification',
                'message': message,
                "data": data,
            }
        )
    #Messages:
    #
    # friend_request_recieved
    # friend_request_accepted
    # friend_request_rejected
    # friend_removed
    #
    #
    # group_invite_recieved
    # group_invite_accepted
    # group_invite_rejected
    # kicked_from_group
    # banned_from_group
    # unbanned_from_group
    # group_name_changed
    # group_host_changed
    # group_deleted




    async def send_notification(self, event):
        message = event["message"]
        data = event["data"]
        print("testing")
        await self.send(text_data=json.dumps({"message": message, "data": data}))