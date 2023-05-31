import io
import os

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from PIL import Image

from photos.models import Photo


class Command(BaseCommand):
    """Rotate all rotated images by actually rotating them as defined in issue #3133 and replacing them in the database with the fixed variant."""

    def handle(self, *args, **options):
        verbosity = options.get("verbosity")

        rotated_photos = Photo.objects.exclude(rotation=0)
        self.stdout.write(
            f"Found {rotated_photos.count()} rotated photos, fixing them..."
        )

        for photo in rotated_photos:
            self.fix_photo(photo, verbosity)

        self.stdout.write("Done!")

    def fix_photo(self, photo, verbosity):
        with photo.file.open() as image_handle:
            image = Image.open(image_handle)
            image.load()

        image = image.rotate(360 - photo.rotation, expand=True)
        photo.rotation = 0

        image_path, _ext = os.path.splitext(photo.original_file)
        image_path = f"{image_path}.jpg"

        buffer = io.BytesIO()
        image.convert("RGB").save(fp=buffer, format="JPEG")
        buff_val = buffer.getvalue()
        content = ContentFile(buff_val)
        photo.file = InMemoryUploadedFile(
            content,
            None,
            image_path,
            "image/jpeg",
            content.tell,
            None,
        )

        photo.save()

        if verbosity >= 2:
            self.stdout.write(f"Fixed photo {photo.pk}")
