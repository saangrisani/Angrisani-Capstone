from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from ai_mhbot.views import home, chat, signup  # <-- add signup

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),  # <-- add this
    path("", home, name="home"),
    path("chat/", chat, name="chat"),
]
