from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Message(models.Model):
    ROLE_CHOICES = (("user", "User"), ("assistant", "Assistant"),)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional: thread/session if you later want multiple chats per user
    # thread_id = models.CharField(max_length=64, blank=True, default="default")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} [{self.role}]: {self.content[:40]}"
