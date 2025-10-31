from django.contrib import admin
from .models import Message, MoodEntry

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "user__username")

@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ("user","mood","created_at")
    search_fields = ("user__username","note")
    list_filter = ("mood","created_at")
