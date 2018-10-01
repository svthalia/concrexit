from django.db.models import When, Value, BooleanField, ExpressionWrapper, Q, \
    Case

from PIL.JpegImagePlugin import JpegImageFile
from PIL import ExifTags


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
        if exif.get('Orientation'):
            return EXIF_ORIENTATION[exif.get('Orientation')]
    return 0


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
        albums = albums.annotate(accessible=ExpressionWrapper(
            Value(True), output_field=BooleanField()))
    elif request.member and request.member.current_membership is None:
        albums_filter = Q(pk__in=[])
        for membership in request.member.membership_set.all():
            albums_filter |= (Q(date__gte=membership.since) & Q(
                date__lte=membership.until))

        albums = albums.annotate(accessible=Case(
            When(albums_filter, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()))
    else:
        albums = albums.annotate(accessible=ExpressionWrapper(
            Value(False), output_field=BooleanField()))

    return albums
