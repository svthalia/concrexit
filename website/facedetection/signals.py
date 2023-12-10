from django.db.models.signals import post_save

from photos.tasks import album_uploaded
from utils.models.signals import suspendingreceiver

from .models import FaceDetectionPhoto, ReferenceFace
from .services import trigger_facedetection_lambda


@suspendingreceiver(
    post_save, sender=ReferenceFace, dispatch_uid="trigger_reference_face_analysis"
)
def trigger_reference_face_analysis(sender, instance, created, **kwargs):
    """Start the facedetection Lambda to extract a face encoding from the reference."""
    if created and instance.status == ReferenceFace.Status.PROCESSING:
        trigger_facedetection_lambda([instance])


@suspendingreceiver(album_uploaded, dispatch_uid="trigger_album_analysis")
def trigger_album_analysis(sender, album, **kwargs):
    """Start the facedetection Lambda on any new photos in the album."""
    photos = FaceDetectionPhoto.objects.bulk_create(
        FaceDetectionPhoto(photo=photo)
        for photo in album.photo_set.filter(
            facedetectionphoto__isnull=True,
        )
    )

    if photos:
        trigger_facedetection_lambda(photos)
