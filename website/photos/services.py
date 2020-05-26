import hashlib
import logging
import os
import tarfile
from zipfile import ZipInfo, is_zipfile, ZipFile

from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.db.models import When, Value, BooleanField, ExpressionWrapper, Q, Case
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from PIL.JpegImagePlugin import JpegImageFile
from PIL import ExifTags, Image, UnidentifiedImageError

from photos.models import Photo

logger = logging.getLogger(__name__)


def photo_determine_rotation(pil_image):
    EXIF_ORIENTATION = {
        1: 0,
        2: 0,
        3: 180,
        4: 180,
        5: 90,
        6: 90,
        7: 270,
        8: 270,
    }

    if isinstance(pil_image, JpegImageFile) and pil_image._getexif():
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in pil_image._getexif().items()
            if k in ExifTags.TAGS
        }
        if exif.get("Orientation"):
            return EXIF_ORIENTATION[exif.get("Orientation")]
    return 0


def check_shared_album_token(album, token):
    if token != album.access_token:
        raise Http404("Invalid token.")


def is_album_accessible(request, album):
    if request.member and request.member.current_membership is not None:
        return True
    elif request.member and request.member.current_membership is None:
        # This user is currently not a member, so need to check if he/she
        # can view this album by checking the membership
        filter = Q(since__lte=album.date) & Q(until__gte=album.date)
        return request.member.membership_set.filter(filter).count() > 0
    return False


# Annotate the albums which are accessible by the user
def get_annotated_accessible_albums(request, albums):
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


def extract_archive(request, album, archive):
    iszipfile = is_zipfile(archive)
    archive.seek(0)

    if iszipfile:
        with ZipFile(archive) as zip_file:
            for photo in sorted(zip_file.infolist(), key=lambda x: x.filename):
                extract_photo(request, zip_file, photo, album)
    else:
        # is_tarfile only supports filenames, so we cannot use that
        try:
            with tarfile.open(fileobj=archive) as tar_file:
                for photo in sorted(tar_file.getmembers(), key=lambda x: x.name):
                    extract_photo(request, tar_file, photo, album)
        except tarfile.ReadError:
            raise ValueError(_("The uploaded file is not a zip or tar file."))


def extract_photo(request, archive_file, photo, album):
    # zipfile and tarfile are inconsistent
    if isinstance(photo, ZipInfo):
        photo_filename = photo.filename
        extract_file = archive_file.open
    elif isinstance(photo, tarfile.TarInfo):
        photo_filename = photo.name
        extract_file = archive_file.extractfile
    else:
        raise TypeError("'photo' must be a ZipInfo or TarInfo object.")

    # Ignore directories
    if not os.path.basename(photo_filename):
        return

    # Generate unique filename
    num = album.photo_set.count()
    filename, extension = os.path.splitext(photo_filename)
    new_filename = str(num).zfill(4) + extension

    photo_obj = Photo()
    photo_obj.album = album
    try:
        with extract_file(photo) as f:
            photo_obj.file.save(new_filename, File(f))

        if not save_photo(photo_obj):
            messages.add_message(
                request, messages.WARNING, _("{} is duplicate.").format(photo_filename)
            )
    except (OSError, AttributeError, UnidentifiedImageError):
        messages.add_message(
            request, messages.WARNING, _("Ignoring {}").format(photo_filename)
        )
        if photo_obj.file.path:
            os.remove(photo_obj.file.path)
        photo_obj.delete()


def save_photo(photo_obj):
    if photo_obj.original_file != photo_obj.file.path:
        original_path = photo_obj.file.path

        image = Image.open(original_path)

        image_path, _ext = os.path.splitext(original_path)
        image_path = "{}.jpg".format(image_path)

        photo_obj.rotation = photo_determine_rotation(image)

        # Image.thumbnail does not upscale an image that is smaller
        image.thumbnail(settings.PHOTO_UPLOAD_SIZE, Image.ANTIALIAS)

        logger.info("Trying to save to %s", image_path)
        image.convert("RGB").save(image_path, "JPEG")
        photo_obj.original_file = image_path
        image_name, _ext = os.path.splitext(photo_obj.file.name)
        photo_obj.file.name = "{}.jpg".format(image_name)

        hash_sha1 = hashlib.sha1()
        for chunk in iter(lambda: photo_obj.file.read(4096), b""):
            hash_sha1.update(chunk)
        photo_obj.file.close()

        digest = hash_sha1.hexdigest()
        photo_obj._digest = digest

        if (
            Photo.objects.filter(album=photo_obj.album, _digest=digest)
            .exclude(pk=photo_obj.pk)
            .exists()
        ):
            photo_obj.delete()
            return False

        photo_obj.save()

        return True
    return False
