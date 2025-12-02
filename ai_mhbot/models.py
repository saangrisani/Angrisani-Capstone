# ai_mhbot/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ------------------------------ MoodEntry ------------------------------
class MoodEntry(models.Model):
    """
    A user's mood snapshot:
    - Persists across visits
    - Tied to a session_id (for continuity per browser session)
    - Includes a 'day' field
    """
    MOODS = [(m, m) for m in ["great", "good", "ok", "sad", "down", "angry", "anxious", "stressed"]]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50, choices=MOODS)
    note = models.TextField(blank=True)

    # ✔ add session continuity + daily snapshot
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    day = models.DateField(default=timezone.localdate, db_index=True)

    # Optional chat context that led to the mood
    chat_user_text = models.TextField(blank=True)
    chat_assistant_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "day"]),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.day} · {self.mood}"

    @staticmethod
    def last_for_user(user):
        """Get the latest mood for quick UI defaults."""
        return (
            MoodEntry.objects
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

# ------------------------------ Message (legacy) ------------------------------
class Message(models.Model):
    """
    Older per-user message log. Kept for compatibility.
    You already use ChatMessage for threaded history; this one can stay or be removed later.
    """
    ROLE_CHOICES = (("user", "User"), ("assistant", "Assistant"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} [{self.role}]: {self.content[:40]}"

# ------------------------------ ChatMessage ------------------------------
class ChatMessage(models.Model):
    ROLE_CHOICES = (("user","user"), ("assistant","assistant"), ("system","system"))
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=64, db_index=True)  # ties anonymous history too
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    meta = models.JSONField(default=dict, blank=True)  # tokens, model, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]
        ordering = ["created_at"]

# ------------------------------ Profile ------------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # Mirrors from signup so Profile has everything
    first_name = models.CharField(max_length=150, blank=True)
    last_name  = models.CharField(max_length=150, blank=True)
    email      = models.EmailField(max_length=254, blank=True)
    phone      = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"

def _sync_profile_from_user(user, profile):
    """Copy data from User -> Profile (one-way)."""
    changed = False
    if profile.first_name != user.first_name:
        profile.first_name = user.first_name; changed = True
    if profile.last_name != user.last_name:
        profile.last_name = user.last_name; changed = True
    if profile.email != user.email:
        profile.email = user.email; changed = True
    if changed:
        profile.save(update_fields=["first_name", "last_name", "email"])

@receiver(post_save, sender=User)
def ensure_and_sync_profile(sender, instance, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    _sync_profile_from_user(instance, profile)

# ------------------------------ LoginEvent ------------------------------
class LoginEvent(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.CharField(max_length=32, choices=[
        ("login_success", "Login Success"),
        ("login_failure", "Login Failure"),
        ("logout", "Logout"),
        ("signup", "Signup"),
    ])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    username_tried = models.CharField(max_length=150, blank=True)

    def __str__(self):
        who = self.user.username if self.user else (self.username_tried or "unknown")
        return f"{self.event} by {who} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"
