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
    """

    location = settings.PUBLIC_MEDIA_LOCATION
    file_overwrite = False
    querystring_auth = False

    # Cloudfront will have a behavior to serve files in PUBLIC_MEDIA_LOCATION publicly,
    # despite the objects in the bucket having a private ACL. Hence, we can use the
    # default "private" ACL to prevent people from reading from the bucket directly.

    def url(self, name, attachment=False, expire_seconds=None):
        params = {}
        if attachment:
            # The S3 bucket will add the Content-Disposition header to the response
            # if the signed URL contains the response-content-disposition query parameter.
            # Cloudfront's cache policy is configured to pass this parameter through to
            # the origin. Otherwise, it wouldn't end up at S3.
            # The `ResponseContentDisposition` parameter as used in the private storage
            # does not work if there's no signature present.
            params[
                "response-content-disposition"
            ] = f'attachment; filename="{attachment}"'

        url = super().url(name, params, expire=expire_seconds)

        return url


class PrivateS3Storage(S3RenameMixin, S3Boto3Storage):
    location = settings.PRIVATE_MEDIA_LOCATION
    file_overwrite = False

    def url(self, name, attachment=False, expire_seconds=None):
        params = {}
        if attachment:
            # Cloudfront will add the Content-Disposition header to the response
            # if the signed URL contains the ResponseContentDisposition query parameter.
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
