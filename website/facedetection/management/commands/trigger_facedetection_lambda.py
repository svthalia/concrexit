from django.core.management.base import BaseCommand

from facedetection.services import (
    resubmit_photos,
    resubmit_reference_faces,
    submit_new_photos,
)


class Command(BaseCommand):
    """Trigger the face detection Lambda function for all images that haven't been processed yet."""

    def handle(self, *args, **options):
        references = resubmit_reference_faces()
        self.stdout.write(f"Resubmitted {len(references)} reference faces.")

        photos = resubmit_photos()
        self.stdout.write(f"Resubmitted {len(photos)} photos.")

        new_photos_count = submit_new_photos()
        self.stdout.write(f"Submitted {new_photos_count} new photos.")
