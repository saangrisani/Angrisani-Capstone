from django.contrib import admin
from .models import ChatMessage, MoodEntry, LoginEvent

# Register your models here.

@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    # Configuration for admin interface
    list_display = ("user","mood","created_at")
    search_fields = ("user__username","note")
    list_filter = ("mood","created_at")
# Admin for LoginEvent model    
@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    # Configuration for admin interface
    list_display = ("timestamp", "event", "user", "ip_address")
    list_filter = ("event", "timestamp")
    search_fields = ("user__username", "ip_address", "username_tried", "user_agent")
    readonly_fields = ("timestamp",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("created_at",)
