import os

import sentry_sdk
from django.conf import settings
from django.core import signing
from django.core.files.storage import get_storage_class, FileSystemStorage, Storage
from storages.backends.s3boto3 import S3Boto3Storage


def get_public_storage():
    return get_storage_class(settings.PUBLIC_FILE_STORAGE)()


class S3AttachmentMixin:
    def url(self, name, attachment=False):
        params = {}
        if attachment:
            params[
                "ResponseContentDisposition"
            ] = f'attachment; filename="{attachment}"'

        return super().url(name, params)


class S3RenameMixin:
    def rename(self, old_name, new_name):
        self.bucket.Object(new_name).copy_from(
            CopySource={"Bucket": self.bucket.name, "Key": old_name}
        )
        self.delete(old_name)

class SentryMixin:
    def path(self, name):
        with sentry_sdk.start_span(op="storage", description="get path"):
            return super().path(name)

    def delete(self, name):
        with sentry_sdk.start_span(op="storage", description="delete file"):
            return super().delete(name)

    def exists(self, name):
        with sentry_sdk.start_span(op="storage", description="file exists"):
            return super().exists(name)

    def listdir(self, path):
        with sentry_sdk.start_span(op="storage", description="listdir"):
            return super().listdir(path)

    def size(self, name):
        with sentry_sdk.start_span(op="storage", description="size"):
            return super().size(name)

    def url(self, name):
        with sentry_sdk.start_span(op="storage", description="url"):
            return super().url(name)

    def get_accessed_time(self, name):
        with sentry_sdk.start_span(op="storage", description="get_accessed_time"):
            return super().get_accessed_time(name)

    def get_created_time(self, name):
        with sentry_sdk.start_span(op="storage", description="get_created_time"):
            return super().get_created_time(name)

    def get_modified_time(self, name):
        with sentry_sdk.start_span(op="storage", description="get_modified_time"):
            return super().get_modified_time(name)


class PublicS3Storage(SentryMixin, S3RenameMixin, S3AttachmentMixin, S3Boto3Storage):
    location = settings.PUBLIC_MEDIA_LOCATION
    file_overwrite = False


class PrivateS3Storage(SentryMixin, S3RenameMixin, S3AttachmentMixin, S3Boto3Storage):
    location = settings.PRIVATE_MEDIA_LOCATION
    file_overwrite = False


class FileSystemRenameMixin:
    def rename(self, old_name, new_name):
        old_name = self.path(old_name)
        new_name = self.path(new_name)
        os.rename(old_name, new_name)


class PublicFileSystemStorage(FileSystemRenameMixin, FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PUBLIC_MEDIA_LOCATION)
    base_url = settings.PUBLIC_MEDIA_URL


class PrivateFileSystemStorage(FileSystemRenameMixin, FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_LOCATION)

    def url(self, name, attachment=False):
        sig_info = {
            "name": name,
            "serve_path": name,
            "storage": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "attachment": attachment,
        }
        return f"{super().url(name)}?sig={signing.dumps(sig_info)}"
