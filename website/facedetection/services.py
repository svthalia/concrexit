import json
import logging
from typing import Union

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

import boto3
from sentry_sdk import capture_exception

from photos.models import Photo
from utils.media.services import get_thumbnail_url

from .models import FaceDetectionPhoto, ReferenceFace

logger = logging.getLogger(__name__)


def execute_data_minimisation(dry_run=False):
    """Delete old reference faces.

    This deletes reference faces that have been marked for deletion by the user for
    some time, as well as reference faces of users that have not logged in for a year.
    """
    delete_period_inactive_member = timezone.now() - timezone.timedelta(days=365)
    delete_period_marked_for_deletion = timezone.now() - timezone.timedelta(
        days=settings.FACEDETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS
    )

    queryset = ReferenceFace.objects.filter(
        Q(marked_for_deletion_at__lte=delete_period_marked_for_deletion)
        | Q(member__last_login__lte=delete_period_inactive_member)
    )

    if not dry_run:
        for reference_face in queryset:
            reference_face.delete()  # Don't run the queryset method, this will also delete the file

    return queryset


def _serialize_lambda_source(source: Union[ReferenceFace, FaceDetectionPhoto]):
    """Serialize a source object to be sent to the lambda function."""
    if isinstance(source, ReferenceFace):
        return {
            "type": "reference",
            "pk": source.pk,
            "token": source.token,
            "photo_url": get_thumbnail_url(
                source.file,
                "medium",
                absolute_url=True,
                # Lambda calls can be queued for up to 6 hours by default, so
                # we make sure the url it uses is valid for at least that long.
                expire_seconds=60 * 60 * 7,
            ),
        }
    if isinstance(source, FaceDetectionPhoto):
        return {
            "type": "photo",
            "pk": source.pk,
            "token": source.token,
            "photo_url": get_thumbnail_url(
                source.photo.file,
                "large",
                absolute_url=True,
                expire_seconds=60 * 60 * 7,
            ),
        }
    raise ValueError("source must be a ReferenceFace or FaceDetectionPhoto")


def _trigger_facedetection_lambda_batch(
    sources: list[Union[ReferenceFace, FaceDetectionPhoto]]
):
    """Submit a batch of sources to the facedetection lambda function.

    If submitting the sources fails, this is logged and
    reported to Sentry, but no exception is raised.
    """
    payload = {
        "api_url": settings.BASE_URL,
        "sources": [_serialize_lambda_source(source) for source in sources],
    }

    for source in sources:
        source.submitted_at = timezone.now()
        source.save()

    try:
        lambda_client = boto3.client(
            service_name="lambda",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        response = lambda_client.invoke(
            FunctionName=settings.FACEDETECTION_LAMBDA_ARN,
            InvocationType="Event",
            Payload=json.dumps(payload),
        )

        if response["StatusCode"] != 202:
            # pylint: disable=broad-exception-raised
            raise Exception("Lambda response was not 202.")

    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error(
            "Submitting sources to lambda failed. Reason: %s", str(e), exc_info=True
        )
        capture_exception(e)


def trigger_facedetection_lambda(
    sources: list[Union[ReferenceFace, FaceDetectionPhoto]]
):
    """Submit a sources to the facedetection lambda function for processing.

    This function will check if the sources are valid and, if a lambda function has
    been configured, try to submit the sources to the lambda function in batches.

    If no lambda function has been configured, or submitting (a batch of) sources fails,
    this is ignored. The sources can be submitted again later.
    """
    if len(sources) == 0:
        raise ValueError("No sources to process.")

    if any(source.status != source.Status.PROCESSING for source in sources):
        raise ValueError("A source has already been processed.")

    if settings.FACEDETECTION_LAMBDA_ARN is None:
        logger.warning(
            "No Lambda ARN has been configured. Sources will not be processed."
        )
        return

    batch_size = settings.FACEDETECTION_LAMBDA_BATCH_SIZE
    for batch in [
        sources[i : i + batch_size] for i in range(0, len(sources), batch_size)
    ]:
        _trigger_facedetection_lambda_batch(batch)


def resubmit_reference_faces() -> list[ReferenceFace]:
    """Resubmit reference faces that (should) have already been submitted but aren't done.

    Returns a list of reference faces that have been resubmitted.
    """
    submitted_before = timezone.now() - timezone.timedelta(hours=7)
    references = list(
        ReferenceFace.objects.filter(
            status=ReferenceFace.Status.PROCESSING,
        ).filter(Q(submitted_at__lte=submitted_before) | Q(submitted_at__isnull=True))
    )
    if references:
        trigger_facedetection_lambda(references)
    return references


def resubmit_photos() -> list[FaceDetectionPhoto]:
    """Resubmit photos that (should) have already been submitted but aren't done.

    Returns a list of photos that have been resubmitted.
    """
    submitted_before = timezone.now() - timezone.timedelta(hours=7)
    photos = list(
        FaceDetectionPhoto.objects.filter(
            status=FaceDetectionPhoto.Status.PROCESSING,
        )
        .filter(Q(submitted_at__lte=submitted_before) | Q(submitted_at__isnull=True))
        .select_related("photo")
    )
    if photos:
        trigger_facedetection_lambda(photos)
    return photos


def submit_new_photos() -> int:
    """Submit photos for which no FaceDetectionPhoto exists yet.

    Returns the number of new photos that have been submitted.
    """
    count = 0
    if not Photo.objects.filter(facedetectionphoto__isnull=True).exists():
        return count

    # We have another level of batching (outside of trigger_facedetection_lambda)
    # for performance and responsive output when there are thousands of photos.
    while Photo.objects.filter(facedetectionphoto__isnull=True).exists():
        photos = FaceDetectionPhoto.objects.bulk_create(
            [
                FaceDetectionPhoto(photo=photo)
                for photo in Photo.objects.filter(facedetectionphoto__isnull=True)[:400]
            ]
        )

        trigger_facedetection_lambda(photos)
        count += len(photos)

    return count
