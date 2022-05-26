import os

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    location = settings.PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False

    def _normalize_name(self, name):
        print(name)
        normalized_value = super()._normalize_name(name)
        print(normalized_value)
        # We replace any double public location strings because of backwards compatibility
        # TODO: Write migration to remove public from file name
        normalized_value = normalized_value.replace("public/public/", "public/")
        return normalized_value


class PrivateMediaStorage(S3Boto3Storage):
    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
