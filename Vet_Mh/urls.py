# Vet_Mh/urls.py
"""
URL routing for the project.

This file was reviewed and tidied up with help from ChatGPT (GPT-5) on 2025-11-06.
- Removed unused imports (TemplateView), duplicate imports, and clutter
- Kept imports explicit and grouped
- Ensured consistent trailing slashes (e.g., mood/add/)
- Left /vets/ as a simple template render for your static page
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.conf import settings


# Import project views explicitly from your app
from ai_mhbot.views import (
    home,
    about,
    resources,
    feedback,
    chat,
    signup,
    profile,
    exercise_breathing,
    exercise_grounding,
    exercise_sleep,
    mood_dashboard,
    mood_add,
    veterans_nearby,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Auth (login/logout/password change)
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="app1/login.html",
            redirect_authenticated_user=False,  # set True if you want to auto-bounce logged-in users
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL),
        name="logout",
    ),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(template_name="app1/password_change.html"),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="app1/password_change_done.html"),
        name="password_change_done",
    ),

    # Signup
    path("signup/", signup, name="signup"),

    # Core pages
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("resources/", resources, name="resources"),
    path("feedback/", feedback, name="feedback"),

    # Profile
    path("profile/", profile, name="profile"),

    # Chat
    path("chat/", chat, name="chat"),

    # Exercises
    path("exercise/breathing/", exercise_breathing, name="exercise_breathing"),
    path("exercise/grounding/", exercise_grounding, name="exercise_grounding"),
    path("exercise/sleep/", exercise_sleep, name="exercise_sleep"),

    # Mood tracker
    path("mood/", mood_dashboard, name="mood_dashboard"),
    path("mood/add/", mood_add, name="mood_add"),  # added trailing slash for consistency

    # Veterans Nearby
    path("vets/", lambda r: render(r, "app1/vets.html"), name="vets_page"),
    path("api/veterans_nearby", veterans_nearby, name="veterans_nearby"),
]
