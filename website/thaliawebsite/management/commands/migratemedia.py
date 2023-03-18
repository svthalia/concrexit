import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

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
            upload_path = self._split_path_to_upload(full_path)
            try:
                try:
                    remote_file = s3_client.head_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=upload_path
                    )
                except ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        remote_file = None
                    else:
                        raise e

                if remote_file:
                    # file already exists
                    # note that this will not check if the file contents are the same
                    print(f"file already exists {upload_path}")
                    logging.info(f"file already exists {upload_path}")
                    continue
                else:
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
