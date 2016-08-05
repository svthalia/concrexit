from django.utils import timezone
from django.utils.six.moves.urllib.parse import unquote

import os


def datetime_to_lectureyear(date):
    sept_1 = timezone.make_aware(timezone.datetime(2016, 9, 1))
    if isinstance(date, timezone.datetime):
        date = date.date()
    if date < sept_1.date():
        return date.year - 1
    return date.year


def sanitize_path(path):
    """Cleans up an insecure path, i.e. against directory traversal.
    This code is partially copied from django.views.static"""
    path = os.path.normpath(unquote(path))
    path = path.lstrip('/')
    newpath = ''
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        newpath = os.path.join(newpath, part).replace('\\', '/')
    return newpath
