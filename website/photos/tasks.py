import logging
import os

from django.db import transaction
from django.dispatch import Signal
from django.utils import timezone

from celery import shared_task
from django_drf_filepond.models import TemporaryUpload, TemporaryUploadChunked
from django_drf_filepond.models import storage as filepond_storage

from mailinglists.services import get_member_email_addresses
from members.models.member import Member
from photos.models import Album
from utils.snippets import send_email

from .services import extract_archive

logger = logging.getLogger(__name__)
album_uploaded = Signal()


@shared_task
def process_album_upload(
    archive_upload_id: str, album_id: int, uploader_id: int | None = None
):
    upload = TemporaryUpload.objects.get(upload_id=archive_upload_id)
    archive = upload.file

    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        logger.exception("Album %s does not exist", album_id)
        archive.delete()
        upload.delete()

    uploader = Member.objects.get(id=uploader_id) if uploader_id is not None else None

    try:
        with transaction.atomic():
            # We make the upload atomic separately, so we can keep using the db if it fails.
            # See https://docs.djangoproject.com/en/4.2/topics/db/transactions/#handling-exceptions-within-postgresql-transactions.
            warnings, count = extract_archive(album, archive)
            album.is_processing = False
            album.save()

            # Send signal to notify that an album has been uploaded. This is used
            # by facedetection, and possibly in the future to notify the uploader.
            album_uploaded.send(sender=None, album=album)

            if uploader is not None:
                # Notify uploader of the upload result.
                send_email(
                    to=get_member_email_addresses(uploader),
                    subject=("Album upload processed completed."),
                    txt_template="photos/email/upload-processed.txt",
                    context={
                        "name": uploader.first_name,
                        "album": album,
                        "upload_name": upload.file.name,
                        "warnings": warnings,
                        "num_processed": count,
                    },
                )
    except Exception as e:
        logger.exception(f"Failed to process album upload: {e}", exc_info=e)

    finally:
        archive.delete()
        upload.delete()


@shared_task
def clean_broken_uploads():
    # Cancel and remove completed uploads that are older than 12 hours.
    for upload in TemporaryUpload.objects.filter(
        uploaded__lte=timezone.now() - timezone.timedelta(hours=12)
    ):
        logger.info(f"Removing old upload {upload.upload_id}")
        upload.file.delete()
        upload.delete()

    # Cancel and remove uploads that have not received new chunks in the last hour.
    for tuc in TemporaryUploadChunked.objects.filter(
        last_upload_time__lt=timezone.now() - timezone.timedelta(hours=1),
    ).exclude(upload_id__in=TemporaryUpload.objects.values("upload_id")):
        logger.info(f"Removing incomplete chunked upload {tuc.upload_id}")
        # Store the chunk and check if we've now completed the upload.
        upload_file = os.path.join(
            tuc.upload_dir, f"{tuc.file_id}_{tuc.last_chunk + 1}"
        )
        filepond_storage.delete(upload_file)
        tuc.delete()
