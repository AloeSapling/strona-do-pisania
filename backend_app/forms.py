from django import forms
from backend_app.models import Message, CustomUser, FriendChat

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'password']
class FriendChatAdd(forms.Form):
    friend = forms.CharField(max_length=150)
    type = forms.ChoiceField(choices={
        'Add':'Add',
        'Delete': 'Delete'
    })
class GroupChatCreate(forms.Form):
    group_name = forms.CharField(max_length=150)