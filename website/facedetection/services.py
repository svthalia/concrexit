import json
from typing import Union

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

import boto3
import requests

from utils.media.services import get_thumbnail_url

from .models import FaceDetectionPhoto, ReferenceFace


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
            "photo_url": get_thumbnail_url(source.file, "medium", absolute_url=True),
        }
    elif isinstance(source, FaceDetectionPhoto):
        return {
            "type": "photo",
            "pk": source.pk,
            "token": source.token,
            "photo_url": get_thumbnail_url(
                source.photo.file, "large", absolute_url=True
            ),
        }


def _trigger_facedetection_lambda_batch(
    sources: list[Union[ReferenceFace, FaceDetectionPhoto]]
):
    """Submit a batch of sources to the facedetection lambda function."""
    payload = {
        "api_url": settings.BASE_URL,
        "sources": [_serialize_lambda_source(source) for source in sources],
    }

    for source in sources:
        source.submitted_at = timezone.now()
        source.save()

    if settings.FACEDETECTION_LAMBDA_ARN:
        session = boto3.session.Session()
        lambda_client = session.client(
            service_name="lambda",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        response = lambda_client.invoke(
            FunctionName=settings.FACEDECTION_LAMBDA_ARN,
            InvocationType="Event",
            Payload=json.dumps(payload),
        )

        if response["StatusCode"] != 202:
            raise Exception("Couldn't invoke Lambda function.")


def trigger_facedetection_lambda(
    sources: list[Union[ReferenceFace, FaceDetectionPhoto]]
):
    if len(sources) == 0:
        raise Exception("No sources to process.")

    if any(source.status != source.Status.PROCESSING for source in sources):
        raise Exception("A source has already been processed.")

    if (
        settings.FACEDETECTION_LAMBDA_ARN is None
        and settings.FACEDETECTION_LAMBDA_URL is None
    ):
        raise Exception("No Lambda ARN or URL configured.")

    batch_size = 20
    for batch in [
        sources[i : i + batch_size] for i in range(0, len(sources), batch_size)
    ]:
        _trigger_facedetection_lambda_batch(batch)
