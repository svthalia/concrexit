from django.db.models import Q
from django.utils import timezone

from facerecognition.models import ReferenceFace
from thaliawebsite import settings


def execute_data_minimisation(dry_run=False):
    """Execute the data minimisation process"""
    delete_period_marked_for_deletion = timezone.now() - timezone.timedelta(
        days=settings.FACE_DETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS
    )
    delete_period_inactive_member = timezone.now() - timezone.timedelta(days=365)
    queryset = ReferenceFace.objects.filter(
        Q(marked_for_deletion_at__lte=delete_period_marked_for_deletion)
        | Q(member__last_login__lte=delete_period_inactive_member)
    )
    if not dry_run:
        for reference_face in queryset:
            reference_face.delete()  # Don't run the queryset method, this will also delete the file
    return queryset
