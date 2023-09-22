import logging

from celery import shared_task

from facedetection.services import (
    resubmit_photos,
    resubmit_reference_faces,
    submit_new_photos,
)

logger = logging.getLogger(__name__)


@shared_task()
def trigger_facedetect_lambda():
    references = resubmit_reference_faces()
    logger.info(f"Resubmitted {len(references)} reference faces.")

    photos = resubmit_photos()
    logger.info(f"Resubmitted {len(photos)} photos.")

    new_photos_count = submit_new_photos()
    logger.info(f"Submitted {new_photos_count} new photos.")
