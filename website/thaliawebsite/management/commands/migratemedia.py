from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings

import logging
import os
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not settings.AWS_STORAGE_BUCKET_NAME:
            logging.error("No AWS settings found")
            return

        # create session to s3
        session = boto3.session.Session()
        s3_client = session.client(
            service_name="s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        # process migrate local media files to s3
        for full_path in self._get_all_media_file():
            try:
                upload_path = self._split_path_to_upload(full_path)
                s3_client.upload_file(
                    full_path, settings.AWS_STORAGE_BUCKET_NAME, upload_path
                )
                print(f"success upload {upload_path}")
                logging.info(f"success upload {upload_path}")
            except ClientError as e:
                print(f"failed upload {upload_path}")
                logging.error(f"{e}: {upload_path}")

    def _get_all_media_file(self) -> [str]:
        files = []
        for r, d, f in os.walk(settings.MEDIA_ROOT):
            for file in f:
                files.append(os.path.join(r, file))
        return files

    def _split_path_to_upload(self, full_path: str) -> str:
        media_root = settings.MEDIA_ROOT
        upload_path = full_path.split(media_root)[-1][1:]
        return upload_path
