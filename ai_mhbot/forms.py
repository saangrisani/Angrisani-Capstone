"""
Forms for account creation and profile updates.

This file was cleaned and organized with help from ChatGPT (GPT-5).
- CustomUserCreationForm extends Django's UserCreationForm
- UserUpdateForm / ProfileUpdateForm for profile page edits
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class CustomUserCreationForm(UserCreationForm):
    """
    Extended sign-up form:
    - first_name, last_name, email (required)
    - phone (optional; stored on Profile)
    """
    first_name = forms.CharField(max_length=150, required=True)
    last_name  = forms.CharField(max_length=150, required=True)
    email      = forms.EmailField(max_length=254, required=True)
    phone      = forms.CharField(max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def clean_email(self):
        """
        Enforce unique email (case-insensitive).
        """
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        """
        Save the User (and ensure Profile exists with phone saved there).
        """
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.email      = self.cleaned_data["email"].strip()
        if commit:
            user.save()

        # Ensure Profile exists, store phone there
        phone = (self.cleaned_data.get("phone") or "").strip()
        profile, _ = Profile.objects.get_or_create(user=user)
        if phone:
            profile.phone = phone
            profile.save(update_fields=["phone"])

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Minimal user update (email only).
    """
    class Meta:
        model  = User
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Profile update (phone only).
    """
    class Meta:
        model  = Profile
        fields = ["phone"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
