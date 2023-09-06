from django.apps import AppConfig


class MoneybirdsynchronizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "moneybirdsynchronization"
    verbose_name = "Moneybird synchronization"

    def ready(self):
        """Import the signals when the app is ready."""
        from . import signals  # noqa: F401
