from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.shortcuts import render
from ai_mhbot.views import veterans_nearby

from ai_mhbot.views import (
    home, chat, signup, about, resources, feedback,
    exercise_breathing, exercise_grounding, exercise_sleep,
    profile, veterans_nearby,
    mood_dashboard, mood_add,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Auth
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="app1/login.html",
            redirect_authenticated_user=False,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="app1/logout.html"),
        name="logout",
    ),
    path("signup/", signup, name="signup"),

    # ChatGPT assist 2025-10-31: add password-change routes
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="app1/password_change.html"
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="app1/password_change_done.html"
        ),
        name="password_change_done",
    ),

    # Pages
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("resources/", resources, name="resources"),
    path("chat/", chat, name="chat"),
    path("feedback/", feedback, name="feedback"),
    path("profile/", profile, name="profile"),

    # Exercises
    path("exercise/breathing/", exercise_breathing, name="exercise_breathing"),
    path("exercise/grounding/", exercise_grounding, name="exercise_grounding"),
    path("exercise/sleep/", exercise_sleep, name="exercise_sleep"),

    # Mood Tracker
    path("mood/", mood_dashboard, name='mood_dashboard'),
    path("mood/add", mood_add, name='mood_add'),

    # Veterans Nearby
    path("vets/", lambda r: render(r, "app1/vets.html"), name="vets_page"),
    path("api/veterans_nearby", veterans_nearby, name="veterans_nearby"),
]
