from django.conf import settings
from utils.templatetags.thumbnail import thumbnail


def create_image_thumbnail_dict(request, file, placeholder='',
                                size_small=settings.THUMBNAIL_SIZES['small'],
                                size_medium=settings.THUMBNAIL_SIZES['medium'],
                                size_large=settings.THUMBNAIL_SIZES['large']):
    if file:
        return {
            'full': request.build_absolute_uri('{}{}'.format(
                settings.MEDIA_URL, file)),
            'small': request.build_absolute_uri(thumbnail(
                file, size_small, 1, True)),
            'medium': request.build_absolute_uri(thumbnail(
                file, size_medium, 1, True)),
            'large': request.build_absolute_uri(thumbnail(
                file, size_large, 1, True))
        }
    return {
        'full': placeholder,
        'small': placeholder,
        'medium': placeholder,
        'large': placeholder,
    }
