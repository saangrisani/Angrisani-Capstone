# Vet_Mh/urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from ai_mhbot.views import (
    home,
    chat,
    signup,
    about,
    resources,
    feedback,
    exercise_breathing,
    exercise_grounding,
    exercise_sleep,
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

    # Pages
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("resources/", resources, name="resources"),
    path("chat/", chat, name="chat"),
    path("feedback/", feedback, name="feedback"),
    path("profile/", TemplateView.as_view(template_name="app1/profile.html"), name="profile"),

    # Exercises
    path("exercise/breathing/", exercise_breathing, name="exercise_breathing"),
    path("exercise/grounding/", exercise_grounding, name="exercise_grounding"),
    path("exercise/sleep/", exercise_sleep, name="exercise_sleep"),
]
