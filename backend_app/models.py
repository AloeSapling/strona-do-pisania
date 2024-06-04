from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import string
import random
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
def generate_unique_code(model, field_name, length=10):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not model.objects.filter(**{field_name: code}).exists():
            return code
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # def create_superuser(self, username, password=None, **extra_fields):
    #     extra_fields.setdefault('is_staff', True)
    #     extra_fields.setdefault('is_superuser', True)

    #     if extra_fields.get('is_staff') is not True:
    #         raise ValueError('Superuser must have is_staff=True.')
    #     if extra_fields.get('is_superuser') is not True:
    #         raise ValueError('Superuser must have is_superuser=True.')

    #     return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractUser):
    name = models.CharField(max_length=255)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username
class Message(models.Model):
    content = models.TextField()
    author = models.ForeignKey('CustomUser', related_name="message_author",on_delete=models.CASCADE)
    edited= models.BooleanField(default=False)
    date_of_creation = timezone.now()
class FriendChat(models.Model):
    users = models.ManyToManyField('CustomUser', related_name="private_chat_users")
    messages = models.ManyToManyField('Message',related_name="private_chat_messages")
    date_of_creation = timezone.now()

    def get_other_user(self, current_user):
        return self.users.exclude(id=current_user.id).first()
class FriendRequestCode(models.Model):
    code = models.CharField(max_length=10, unique=True, default=None, null=True)
    user = models.ForeignKey('CustomUser', related_name="code_request_user",on_delete=models.CASCADE)
    available = models.BooleanField(default=True)
    date_of_creation = timezone.now()
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_unique_code(FriendRequestCode, 'code')
        super(FriendRequestCode, self).save(*args, **kwargs)
class FriendRequestPrivate(models.Model):
    to_user = models.ForeignKey('CustomUser', related_name='friend_private_to_user',on_delete=models.CASCADE)
    from_user = models.ForeignKey('CustomUser', related_name='friend_private_from_user', on_delete=models.CASCADE)
    available = models.BooleanField(default=True)
    date_of_creation = timezone.now()
class GroupInvitePrivate(models.Model):
    group = models.ForeignKey('GroupChat',related_name='private_invite_group', on_delete=models.CASCADE)
    to_user = models.ForeignKey('CustomUser', related_name='group_private_to_user',on_delete=models.CASCADE)
    from_user = models.ForeignKey('CustomUser', related_name='group_private_from_user', on_delete=models.CASCADE)
    date_of_creation = timezone.now()
class GroupInviteCode(models.Model):
    group = models.ForeignKey('GroupChat',related_name='code_invite_group', on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True, default=None, null=True)
    from_user = models.ForeignKey('CustomUser', related_name='group_code_from_user', on_delete=models.CASCADE)
    date_of_creation = timezone.now()
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_unique_code(GroupInviteCode, 'code')
        super(GroupInviteCode, self).save(*args, **kwargs)
class GroupChat(models.Model):
    name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    users = models.ManyToManyField('CustomUser',related_name="group_users")
    new_users = models.ManyToManyField('CustomUser', related_name="group_new_users")
    host = models.ForeignKey('CustomUser', related_name='group_host',on_delete=models.CASCADE)
    messages = models.ManyToManyField('Message', related_name="group_messages")
    date_of_creation = timezone.now()
@receiver(m2m_changed, sender=GroupChat.users.through)
def add_to_new_users(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == "post_add":
        for user_pk in pk_set:
            user = model.objects.get(pk=user_pk)
            instance.new_users.add(user)

class BanList(models.Model):
    group = models.ForeignKey('GroupChat', related_name="ban_group", on_delete=models.CASCADE)
    user = models.ForeignKey('CustomUser', related_name='banned_user',on_delete=models.CASCADE)
    date_of_creation = timezone.now()
class Notification(models.Model):
    message = models.TextField
    for_user = models.ForeignKey('CustomUser', related_name="notification_for_user", on_delete=models.CASCADE)
    date_of_creation = timezone.now()