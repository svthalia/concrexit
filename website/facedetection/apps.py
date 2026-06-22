from django.apps import AppConfig
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FaceDetectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "facedetection"
    verbose_name = _("Face detection")

    def user_menu_items(self):
        return {
            "items": [
                {
                    "section": "profile",
                    "title": "Your photos",
                    "url": reverse("facedetection:your-photos"),
                    "key": 2,
                },
            ],
        }

    def ready(self):
        """Register signals when the app is ready."""
        from . import signals  # noqa: F401

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        """Delete old reference faces.

        This deletes reference faces that have been marked for deletion by the user for
        some time, as well as reference faces of users that have not logged in for a year.
        """
        from .models import ReferenceFace

        delete_period_inactive_member = timezone.now() - timezone.timedelta(days=365)
        delete_period_marked_for_deletion = timezone.now() - timezone.timedelta(
            days=settings.FACEDETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS
        )

        queryset = ReferenceFace.objects.filter(
            Q(marked_for_deletion_at__lte=delete_period_marked_for_deletion)
            | Q(user__last_login__lte=delete_period_inactive_member)
        )

        if not dry_run:
            for reference_face in queryset:
                reference_face.delete()  # Don't run the queryset method, this will also delete the file

        return queryset
