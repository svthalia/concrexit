import logging

from django.db import transaction
from django.dispatch import Signal

from celery import shared_task
from django_drf_filepond.models import TemporaryUpload

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
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        return

    uploader = Member.objects.get(id=uploader_id) if uploader_id is not None else None

    upload = TemporaryUpload.objects.get(upload_id=archive_upload_id)
    archive = upload.file
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
