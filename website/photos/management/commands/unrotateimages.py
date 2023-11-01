import io

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from PIL import Image

from photos.models import Photo
from website.thaliawebsite.storage.backend import PrivateS3Storage, PublicS3Storage


class _ForceOverwritePrivateS3Storage(PrivateS3Storage):
    file_overwrite = True


class _ForceOverwritePublicS3Storage(PublicS3Storage):
    file_overwrite = True


class Command(BaseCommand):
    """Clear the rotation field on all photos, withoout the downtime of doing this in a migration.

    This can be removed once a migration has been applied that drops the rotation field.
    """

    def handle(self, *args, **options):
        verbosity = options.get("verbosity")
        for photo in Photo.objects.all():
            if verbosity >= 2:
                self.stdout.write(f"Unrotating {photo.file.name}.")

            photo.file.thumbnails.delete_all()

            with photo.file.open() as image_handle:
                image = Image.open(image_handle)
                image.load()

            image = image.rotate(360 - photo.rotation, expand=True)
            photo.rotation = 0

            buffer = io.BytesIO()
            image.convert("RGB").save(fp=buffer, format="JPEG")
            buff_val = buffer.getvalue()
            content = ContentFile(buff_val)
            photo.file = InMemoryUploadedFile(
                content, None, "photo.jpg", "image/jpeg", content.tell, None
            )

            # Make sure the existing photo is overwritten by replacing the
            # storage that doesn't overwrite on S3, with one that does.
            if isinstance(photo.file.storage, PrivateS3Storage):
                photo.file.storage = _ForceOverwritePrivateS3Storage()
            elif isinstance(photo.file.storage, PublicS3Storage):
                photo.file.storage = _ForceOverwritePublicS3Storage()

            photo.save()
