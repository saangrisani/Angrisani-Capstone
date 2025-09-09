from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from ai_mhbot.views import home, chat, signup, about, resources

urlpatterns = [
    path("admin/", admin.site.urls),
    #authorization urls
    path("login/",  auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    #my application webpages
    path("", home, name="home"),
    path("chat/", chat, name="chat"),
    path("signup/", signup, name="signup"),
    path("about/", about, name="about"),
    path("resources/", resources, name="resources"),
]