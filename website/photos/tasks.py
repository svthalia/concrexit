from django.db import transaction

from celery import shared_task
from django_drf_filepond.models import TemporaryUpload
from django_filepond_widget.fields import FilePondFile

from photos.models import Album

from .services import extract_archive


@shared_task
def process_album_upload(archive_upload_id: str, album_id: int):
    archive = TemporaryUpload.objects.get(upload_id=archive_upload_id).file
    try:
        album = Album.objects.get(id=album_id)
        with transaction.atomic():
            # We make the upload atomic separately, so we can keep using the db if it fails.
            # See https://docs.djangoproject.com/en/4.2/topics/db/transactions/#handling-exceptions-within-postgresql-transactions.
            extract_archive(album, archive)
            album.is_processing = False
            album.save()
            # In the future, we might want to notify the uploader here.
    except Exception:
        raise
    finally:
        if isinstance(archive, FilePondFile):
            archive.remove()
