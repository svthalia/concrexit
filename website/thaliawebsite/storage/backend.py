import os

from django.conf import settings
from django.core import signing
from django.core.files.storage import get_storage_class, FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


def get_public_storage():
    return get_storage_class(settings.PUBLIC_FILE_STORAGE)()


class S3AttachmentMixin:
    def url(self, name, attachment=False):
        params = {}
        if attachment:
            params[
                "ResponseContentDisposition"
            ] = f'attachment; filename="{os.path.basename(name)}"'

        return super().url(name, params)


class PublicS3Storage(S3Boto3Storage, S3AttachmentMixin):
    location = settings.PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False


class PrivateS3Storage(S3Boto3Storage, S3AttachmentMixin):
    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False


class PublicFileSystemStorage(FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PUBLIC_MEDIA_LOCATION)
    base_url = settings.PUBLIC_MEDIA_URL


class PrivateFileSystemStorage(FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_LOCATION)

    def url(self, name, attachment=False):
        sig_info = {
            "name": name,
            "serve_path": name,
            "storage": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "attachment": attachment,
        }
        return f"{self.url(name)}?sig={signing.dumps(sig_info)}"
