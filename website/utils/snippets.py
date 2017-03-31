import os

from django.utils import timezone
from django.utils.six.moves.urllib.parse import unquote


def datetime_to_lectureyear(date):
    """Convert a date to the start of the lectureyear

    >>> from datetime import date, datetime, timezone
    >>> nov_23 = date(1990, 11, 7)
    >>> datetime_to_lectureyear(nov_23)
    1990
    >>> mar_2 = date(1993, 3, 2)
    >>> datetime_to_lectureyear(mar_2)
    1992

    Also works on ``datetimes``, but they need to be tz-aware:

    >>> new_year = datetime(2000, 1, 1, tzinfo=timezone.utc)
    >>> datetime_to_lectureyear(new_year)
    1999
    """

    if isinstance(date, timezone.datetime):
        date = timezone.localtime(date).date()
    sept_1 = timezone.make_aware(timezone.datetime(date.year, 9, 1))
    if date < sept_1.date():
        return date.year - 1
    return date.year


def sanitize_path(path):
    r"""
    Cleans up an insecure path, i.e. against directory traversal.

    Still use os.path.commonprefix to check if the target is as expected

    This code is partially copied from ``django.views.static``.

    >>> sanitize_path('//////')
    ''
    >>> sanitize_path('////test//')
    'test'
    >>> sanitize_path('../../../test/')
    'test'
    >>> sanitize_path('../.././test/')
    'test'
    >>> sanitize_path(r'..\..\..\test')
    'test'

    """
    path = os.path.normpath(unquote(path).replace('\\', '/'))
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
        newpath = os.path.join(newpath, part)
    return newpath


if __name__ == "__main__":
    import doctest
    doctest.testmod()
