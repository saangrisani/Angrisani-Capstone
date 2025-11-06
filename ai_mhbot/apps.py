from django.apps import AppConfig

# App configuration for ai_mhbot
class AiMhbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_mhbot"

    def ready(self):
        # Registers signal handlers when the app loads.
        # This import path and integration were added with help from ChatGPT (GPT-5).
        from . import signals
