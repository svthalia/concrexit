from thaliawebsite.settings import settings
from utils.templatetags.thumbnail import thumbnail


def create_image_thumbnail_dict(request, file, placeholder='',
                                size_small='110x110', size_medium='220x220',
                                size_large='1024x768'):
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
