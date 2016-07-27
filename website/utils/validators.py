from django.core.exceptions import ValidationError

import os


def validate_file_extension(file, exts=['.txt', '.pdf', '.jpg', '.png']):
    _, ext = os.path.splitext(file.name)
    if not ext.lower() in exts:
        raise ValidationError("File extension not allowed.")
