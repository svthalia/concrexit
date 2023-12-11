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
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        return

    archive = TemporaryUpload.objects.get(upload_id=archive_upload_id).file
    try:
        with transaction.atomic():
            # We make the upload atomic separately, so we can keep using the db if it fails.
            # See https://docs.djangoproject.com/en/4.2/topics/db/transactions/#handling-exceptions-within-postgresql-transactions.
            extract_archive(album, archive)
            album.is_processing = False
            album.save()

            # Send signal to notify that an album has been uploaded. This is used
            # by facedetection, and possibly in the future to notify the uploader.
            album_uploaded.send(sender=None, album=album)
    finally:
        if isinstance(archive, FilePondFile):
            archive.remove()
