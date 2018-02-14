"""Validators for form fields"""
import os

from django.core.exceptions import ValidationError


def validate_file_extension(file, exts=None):
    """
    Checks if a file has a certain allowed extension. Raises a
    :class:`~django.core.exceptions.ValidationError` if that's not the case.

    :param file: the file to validate
    :param list(str) exts: the list of acceptable types.
        Default: ``.txt``, ``.pdf``, ``.jpg``, ``.jpeg``, ``.png``.
    :raises ValidationError: if the extension is not allowed.

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
    if exts is None:
        exts = ['.txt', '.pdf', '.jpg', '.jpeg', '.png']
    ext = os.path.splitext(file.name)[1]
    if not ext.lower() in exts:
        raise ValidationError("File extension not allowed.")
