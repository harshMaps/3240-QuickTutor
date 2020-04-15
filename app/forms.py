from django import forms
from .models import User

class RequestForm(forms.Form):
    title = forms.CharField(label='Title', max_length=100)  # the title of the request
    location = forms.CharField(max_length=200)  # the location of the tutee (as specified by the tutee)
    pub_date = forms.DateTimeField()  # when it was published
    description = forms.CharField(max_length=1000)  # a description written by the tutee

class UserUpdateForm(forms.ModelForm):
    # can only update name, username, profile pic, bio
    class Meta:
        model = User
        fields = ['username','description', 'image']