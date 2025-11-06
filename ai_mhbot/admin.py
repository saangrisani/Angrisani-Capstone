from django.contrib import admin
from .models import Message, MoodEntry, LoginEvent
# Register your models here.
# Admin for Message model

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
