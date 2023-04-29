from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

import requests

from photos.models import Photo
from utils.media.services import get_media_url

from .models import FaceEncodedPhoto


@receiver(post_save, sender=Photo)
def trigger_image_analysis(sender, instance, **kwargs):
    """Start a Lambda function that will extract face encodings from the Photo."""

    if hasattr(instance, "faceencodedphoto"):
        return

    encoded_photo = FaceEncodedPhoto.objects.create(photo=instance)

    body = {
        "photo_pk": instance.pk,
        "photo_url": get_media_url(instance.file, absolute_url=True),
        "token": encoded_photo.token,
    }

    requests.post(settings.FACE_DETECTION_LAMBDA_URL, json=body)


# TODO: Also need a function (though probably not a signal, as it's internal
# to the facedetection app) that submits the reference photo to lambda.
