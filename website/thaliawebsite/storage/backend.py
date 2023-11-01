import os

from django.conf import settings
from django.core import signing
from django.core.files.storage import FileSystemStorage

from storages.backends.s3boto3 import S3Boto3Storage, S3ManifestStaticStorage


class S3RenameMixin:
    def rename(self, old_name, new_name):
        self.bucket.Object(new_name).copy_from(
            CopySource={"Bucket": self.bucket.name, "Key": old_name}
        )
        self.delete(old_name)


class PublicS3Storage(S3RenameMixin, S3Boto3Storage):
    """Storage on S3 for public media files.

    This storage is used for files that are publicly accessible. We use CloudFront to
    serve files from S3. CloudFront is configured with a behavior to serve files in the
    PUBLIC_MEDIA_LOCATION publicly, despite the objects in the bucket having a "private"
    ACL. Hence, we can still use the default "private" ACL to prevent people from using
    the S3 bucket directly.

    To support the "ResponseContentDisposition" parameter for the `attachment` argument
    to `PublicS3Storage.url` we do still need to sign the url, but in other cases we can
    strip the signing parameters from urls.
    """

    location = settings.PUBLIC_MEDIA_LOCATION
    file_overwrite = False

    # Cloudfront will have a behavior to serve files in PUBLIC_MEDIA_LOCATION publicly,
    # despite the objects in the bucket having a private ACL. Hence, we can use the
    # default "private" ACL to prevent people from reading from the bucket directly.

    def url(self, name, attachment=False, expire_seconds=None):
        params = {}
        if attachment:
            params[
                "ResponseContentDisposition"
            ] = f'attachment; filename="{attachment}"'

        url = super().url(name, params, expire=expire_seconds)

        if not attachment:
            # The signature is required even for public media in order
            # to support the "ResponseContentDisposition" parameter.
            return self._strip_signing_parameters(url)

        return url


class PrivateS3Storage(S3RenameMixin, S3Boto3Storage):
    location = settings.PRIVATE_MEDIA_LOCATION
    file_overwrite = False

    def url(self, name, attachment=False, expire_seconds=None):
        params = {}
        if attachment:
            params[
                "ResponseContentDisposition"
            ] = f'attachment; filename="{attachment}"'

        return super().url(name, params, expire=expire_seconds)


class StaticS3Storage(S3ManifestStaticStorage):
    location = settings.STATICFILES_LOCATION
    object_parameters = {"CacheControl": "max-age=31536000"}

    # Clear the signing information as we don't need it for static files.
    # Loading the cloudfront key would waste some time for no reason.
    cloudfront_key_id = None
    cloudfront_key = None


class FileSystemRenameMixin:
    def rename(self, old_name, new_name):
        old_name = self.path(old_name)
        new_name = self.path(new_name)
        os.rename(old_name, new_name)


class PublicFileSystemStorage(FileSystemRenameMixin, FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PUBLIC_MEDIA_LOCATION)
    base_url = settings.PUBLIC_MEDIA_URL

    def url(self, name, attachment=False, expire_seconds=None):
        return super().url(name)


class PrivateFileSystemStorage(FileSystemRenameMixin, FileSystemStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_LOCATION)

    def url(
        self,
        name,
        attachment=False,
        expire_seconds=None,
    ):
        sig_info = {
            "name": name,
            "serve_path": name,
            "storage": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "attachment": attachment,
        }
        return f"{super().url(name)}?sig={signing.dumps(sig_info)}"
