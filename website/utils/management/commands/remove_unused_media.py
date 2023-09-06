import os

from django.apps import apps
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.management.base import BaseCommand
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.utils import timezone

from thaliawebsite.storage.backend import get_public_storage


def get_file_fields():
    """Get all FileFields of all models."""
    all_models = apps.get_models()
    fields = []
    for model in all_models:
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField):
                fields.append(field)
    return fields


def remove_empty_dirs(path=None):
    """Remove the directory `path` if it is emty, and return whether it was removed."""
    if not path:
        path = settings.MEDIA_ROOT

    if not os.path.isdir(path):
        return False

    listdir = [os.path.join(path, filename) for filename in os.listdir(path)]

    if all(list(map(remove_empty_dirs, listdir))):
        os.rmdir(path)
        return True
    return False


def get_used_media(storage):
    """Get the filenames of all files stored in a FileField of any model."""
    media = set()

    for field in get_file_fields():
        is_null = {
            f"{field.name}__isnull": True,
        }
        is_empty = {
            f"{field.name}": "",
        }

        if not isinstance(field.storage, type(storage)):
            continue

        for value in (
            field.model._base_manager.values_list(field.name, flat=True)
            .exclude(**is_empty)
            .exclude(**is_null)
        ):
            if value not in EMPTY_VALUES:
                media.add(value)

    return media


def get_all_media(storage, minimum_file_age=None, folder=""):
    media = set()
    initial_time = timezone.now()

    if not storage.exists(folder):
        return []

    dirs, files = storage.listdir(folder)

    # Remove file locations in case they are nested
    # (public is in the private media dir at the time of writing this code)
    if settings.PUBLIC_MEDIA_LOCATION in dirs:
        dirs.remove(settings.PUBLIC_MEDIA_LOCATION)
    if settings.PRIVATE_MEDIA_LOCATION in dirs:
        dirs.remove(settings.PRIVATE_MEDIA_LOCATION)

    for name in files:
        name = os.path.join(folder, name)
        if minimum_file_age:
            file_age = initial_time - storage.get_modified_time(name)

            if file_age.total_seconds() < minimum_file_age:
                continue
        else:
            media.add(name)

    for name in dirs:
        media.update(
            get_all_media(storage, minimum_file_age, os.path.join(folder, name))
        )

    return media


def get_unused_media(storage, minimum_file_age=None):
    all_media = get_all_media(storage, minimum_file_age)
    used_media = get_used_media(storage)

    return all_media - used_media


class Command(BaseCommand):
    help = "Clean unused media files which have no reference in models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            dest="interactive",
            action="store_false",
            default=True,
            help="Do not ask confirmation",
        )

        parser.add_argument(
            "--minimum-file-age",
            dest="minimum_file_age",
            default=180,
            type=int,
            help="Skip files younger this age (sec)",
        )

        parser.add_argument(
            "-n",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            default=False,
            help="Dry run without any affect on your data",
        )

    def _show_files_to_delete(self, storage_type, unused_media, verbosity):
        if verbosity >= 2:
            self.stdout.writelines(map(lambda x: f"Will remove {x}", unused_media))

        self.stdout.write(
            f"Total {storage_type} files to be removed: {len(unused_media)}"
        )

    def handle(self, *args, **options):
        verbosity = options.get("verbosity")

        private_storage = DefaultStorage()
        unused_private_media = get_unused_media(
            private_storage,
            minimum_file_age=options.get("minimum_file_age"),
        )

        public_storage = get_public_storage()
        unused_public_media = get_unused_media(
            public_storage,
            minimum_file_age=options.get("minimum_file_age"),
        )

        if not unused_public_media and not unused_private_media:
            self.stdout.write("Nothing to delete. Exit")
            return

        if options.get("dry_run"):
            self._show_files_to_delete("private", unused_private_media, verbosity)
            self._show_files_to_delete("public", unused_public_media, verbosity)
            self.stdout.write("Dry run. Exit.")
            return

        if options.get("interactive"):
            self._show_files_to_delete("private", unused_private_media, verbosity)
            self._show_files_to_delete("public", unused_public_media, verbosity)

            question = f"Are you sure you want to remove {len(unused_private_media) + len(unused_public_media)} unused files? (y/N)"

            if input(question).upper() != "Y":
                self.stdout.write("Interrupted by user. Exit.")
                return

        for f in unused_private_media:
            private_storage.delete(f)

        for f in unused_public_media:
            public_storage.delete(f)

        remove_empty_dirs()

        self.stdout.write(
            f"Done. Total files removed: {len(unused_private_media) + len(unused_public_media)}"
        )
