from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Required")
    last_name = forms.CharField(max_length=30, required=True, help_text="Required")
    email = forms.EmailField(max_length=254, required=True, help_text="Required. Enter a valid email address.")

class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
             "username": forms.TextInput(attrs={"class": "form-control"}),
             "email": forms.EmailInput(attrs={"class": "form-control"})
        }