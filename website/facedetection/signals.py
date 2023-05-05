from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ReferenceFace
from .services import trigger_facedetection_lambda


@receiver(
    post_save, sender=ReferenceFace, dispatch_uid="trigger_reference_face_analysis"
)
def trigger_reference_face_analysis(sender, instance, created, **kwargs):
    """Start the facedetection Lambda to extract a face encoding from the reference."""
    if created and instance.status == ReferenceFace.Status.PROCESSING:
        trigger_facedetection_lambda([instance])
