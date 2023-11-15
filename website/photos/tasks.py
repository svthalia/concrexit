from django.db import transaction
from django.dispatch import Signal

from celery import shared_task
from django_drf_filepond.models import TemporaryUpload
from django_filepond_widget.fields import FilePondFile

from photos.models import Album

from .services import extract_archive

album_uploaded = Signal()


@shared_task
def process_album_upload(archive_upload_id: str, album_id: int):
    archive = TemporaryUpload.objects.get(upload_id=archive_upload_id).file
    album = Album.objects.get(id=album_id)
    print(album, archive)
    try:
        with transaction.atomic():
            # We make the upload atomic separately, so we can keep using the db if it fails.
            # See https://docs.djangoproject.com/en/4.2/topics/db/transactions/#handling-exceptions-within-postgresql-transactions.
            extract_archive(album, archive)
        album_uploaded.send(sender=None, album=album)
    except Exception:
        raise
    finally:
        if isinstance(archive, FilePondFile):
            archive.remove()

    # Open archive.
    # Extract each photo.
    # Create thumbnails (we can set `pregenerate_sizes` on the Photo.file ImageField).

    # Set status = ready.
    # Notify uploader?
    # delete archive
