from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from facedetection.models import FaceDetectionPhoto, ReferenceFace
from facedetection.services import trigger_facedetection_lambda
from photos.models import Photo


class Command(BaseCommand):
    """Trigger the face detection Lambda function for all images that haven't been processed yet."""

    def handle(self, *args, **options):
        self._resubmit_reference_faces()
        self._resubmit_photos()
        self._submit_new_photos()

    def _resubmit_reference_faces(self):
        """Resubmit reference faces that (should) have already been submitted but aren't done."""
        submitted_before = timezone.now() - timezone.timedelta(hours=7)
        references = list(
            ReferenceFace.objects.filter(
                status=ReferenceFace.Status.PROCESSING,
            ).filter(
                Q(submitted_at__lte=submitted_before) | Q(submitted_at__isnull=True)
            )
        )
        self.stdout.write(f"Resubmitting {len(references)} reference faces.")
        trigger_facedetection_lambda(references)

    def _resubmit_photos(self):
        """Resubmit photos that (should) have already been submitted but aren't done."""
        submitted_before = timezone.now() - timezone.timedelta(hours=7)
        photos = list(
            FaceDetectionPhoto.objects.filter(
                status=FaceDetectionPhoto.Status.PROCESSING,
            )
            .filter(
                Q(submitted_at__lte=submitted_before) | Q(submitted_at__isnull=True)
            )
            .select_related("photo")
        )
        self.stdout.write(f"Resubmitting {len(photos)} photos.")
        trigger_facedetection_lambda(photos)

    def _submit_new_photos(self):
        """Submit photos for which no FaceDetectionPhoto exists yet."""
        if not Photo.objects.filter(facedetectionphoto__isnull=True).exists():
            self.stdout.write("No new photos to submit.")
            return

        # We have another level of batching (outside of trigger_facedetection_lambda)
        # for performance and responsive output when there are thousands of photos.
        while Photo.objects.filter(facedetectionphoto__isnull=True).exists():
            self.stdout.write("Creating new FaceDetectionPhotos.")
            photos = FaceDetectionPhoto.objects.bulk_create(
                [
                    FaceDetectionPhoto(photo=photo)
                    for photo in Photo.objects.filter(facedetectionphoto__isnull=True)[
                        :400
                    ]
                ]
            )

            self.stdout.write(f"Submitting {len(photos)} photos.")
            trigger_facedetection_lambda(photos)
