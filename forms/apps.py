from django.apps import AppConfig

class FormsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forms"

    def ready(self):
        # Ensure signal handlers are registered
        import forms.signals  # noqa: F401
