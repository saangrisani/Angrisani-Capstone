# ai_mhbot/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name  = forms.CharField(max_length=150, required=True)
    email      = forms.EmailField(max_length=254, required=True)
    phone      = forms.CharField(max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.email      = self.cleaned_data["email"].strip()
        if commit:
            user.save()

        # Ensure Profile exists & store phone there
        phone = (self.cleaned_data.get("phone") or "").strip()
        profile, _ = Profile.objects.get_or_create(user=user)
        if phone:
            profile.phone = phone
            profile.save(update_fields=["phone"])

        # The post_save signal syncs first/last/email onto Profile automatically
        return user
    
    # ChatGPT assist 2025-10-31: profile + user update forms
from django.contrib.auth.models import User

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]  # we only let them change email here
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
