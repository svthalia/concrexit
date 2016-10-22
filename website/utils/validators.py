import os

from django.core.exceptions import ValidationError


def validate_file_extension(file, exts=['.txt', '.pdf', '.jpg', '.png']):
    ext = os.path.splitext(file.name)[1]
    if not ext.lower() in exts:
        raise ValidationError("File extension not allowed.")
