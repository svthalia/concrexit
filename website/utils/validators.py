import os

from django.core.exceptions import ValidationError


def validate_file_extension(file,
                            exts=['.txt', '.pdf', '.jpg', '.jpeg', '.png']):
    """
    Checks if a file has a certain allowed extension. Raises a
    ``ValidationError`` if that's not the case.

    >>> class File(object):
    ...   pass
    >>> f = File()
    >>> f.name = 'foo.jpeg'
    >>> validate_file_extension(f)
    >>> f.name = 'foo.exe'
    >>> validate_file_extension(f)
    Traceback (most recent call last):
        ...
    django.core.exceptions.ValidationError: ['File extension not allowed.']
    >>> validate_file_extension(f, ['.exe'])
    """
    ext = os.path.splitext(file.name)[1]
    if not ext.lower() in exts:
        raise ValidationError("File extension not allowed.")
