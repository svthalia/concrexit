import logging
import os
import tarfile
from zipfile import ZipFile, is_zipfile

from django.core.files import File
from django.db import transaction
from django.db.models import BooleanField, Case, ExpressionWrapper, Q, Value, When
from django.forms import ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from PIL import UnidentifiedImageError

from photos.models import Photo

logger = logging.getLogger(__name__)


def check_shared_album_token(album, token):
    """Return a 404 if the token does not match the album token."""
    if token != album.access_token:
        raise Http404("Invalid token.")


def is_album_accessible(request, album):
    """Check if the request user can access an album."""
    if request.member and request.member.current_membership is not None:
        return True
    if request.member and request.member.current_membership is None:
        # This user is currently not a member, so need to check if he/she
        # can view this album by checking the membership
        return request.member.membership_set.filter(
            Q(since__lte=album.date) & Q(until__gte=album.date)
        ).exists()
    return False


def get_annotated_accessible_albums(request, albums):
    """Annotate the albums which are accessible by the user."""
    if request.member and request.member.current_membership is not None:
        albums = albums.annotate(
            accessible=ExpressionWrapper(Value(True), output_field=BooleanField())
        )
    elif request.member and request.member.current_membership is None:
        albums_filter = Q(pk__in=[])
        for membership in request.member.membership_set.all():
            albums_filter |= Q(date__gte=membership.since) & Q(
                date__lte=membership.until
            )

        albums = albums.annotate(
            accessible=Case(
                When(albums_filter, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
    else:
        albums = albums.annotate(
            accessible=ExpressionWrapper(Value(False), output_field=BooleanField())
        )

    return albums


def extract_archive(album, archive) -> tuple[dict[str, str], int]:
    """Extract zip and tar files."""
    warnings, count = {}, 0
    if is_zipfile(archive):
        archive.seek(0)
        with ZipFile(archive) as zip_file:
            for photo in sorted(zip_file.namelist()):
                if not _has_photo_extension(photo):
                    warnings[photo] = "has an unknown extension."
                    continue

                with zip_file.open(photo) as file:
                    if warning := _try_save_photo(album, file, photo):
                        warnings[photo] = warning
                    else:
                        count += 1
        return warnings, count

    archive.seek(0)
    # is_tarfile only supports filenames, so we cannot use that
    try:
        with tarfile.open(fileobj=archive) as tar_file:
            for photo in sorted(tar_file.getnames()):
                if not _has_photo_extension(photo):
                    warnings[photo] = "has an unknown extension."
                    continue

                with tar_file.extractfile(photo) as file:
                    if warning := _try_save_photo(album, file, photo):
                        warnings[photo] = warning
                    else:
                        count += 1
    except tarfile.ReadError as e:
        raise ValueError(_("The uploaded file is not a zip or tar file.")) from e

    return warnings, count


def _has_photo_extension(filename):
    """Check if the filename has a photo extension."""
    __, extension = os.path.splitext(filename)
    return extension.lower() in (".jpg", ".jpeg", ".png", ".webp")


def _try_save_photo(album, file, filename) -> str | None:
    """Try to save a photo to an album.

    Returns None, or a string describing a reason for failure.
    """
    instance = Photo(album=album)
    instance.file = File(file, filename)
    try:
        with transaction.atomic():
            instance.full_clean()
            instance.save()
    except ValidationError as e:
        logger.warning(f"Photo '{filename}' could not be read: {e}", exc_info=e)
        return "could not be read."
    except UnidentifiedImageError as e:
        logger.warning(f"Photo '{filename}' could not be read: {e}", exc_info=e)
        return "could not be read."
    except OSError as e:
        logger.warning(f"Photo '{filename}' could not be read: {e}", exc_info=e)
        return "could not be read."
