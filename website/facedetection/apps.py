from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FaceDetectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "facedetection"
    verbose_name = _("Face detection")

    def ready(self):
        """Register signals when the app is ready."""
        from . import signals  # noqa: F401
