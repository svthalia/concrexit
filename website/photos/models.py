from django.utils.text import slugify
from django.conf import settings
from django.utils.functional import cached_property

import os
import re
from datetime import datetime
import random
from functools import total_ordering

COVER_FILENAME = 'cover.jpg'


@total_ordering
class Album(object):

    photosdir = 'photos'
    photospath = os.path.join(settings.MEDIA_ROOT, photosdir)

    def __init__(self, dirname):
        date, self.title = dirname.split('_')
        # This supports both 1990-11-07_albumname as well as 19901107_albumname
        self.date = datetime.strptime(re.sub(r"\D", "", date), '%Y%m%d')
        self.dirname = dirname
        self.path = os.path.join(Album.photospath, self.dirname)

    @cached_property
    def slug(self):
        return slugify('{}-{}'.format(self.date.strftime('%Y-%m-%d'),
                                      self.title))

    @cached_property
    def cover(self):
        if os.path.isfile(os.path.join(self.path, COVER_FILENAME)):
            cover = COVER_FILENAME
        else:
            random.seed(self.dirname)
            cover = random.choice(os.listdir(self.path))
        return os.path.join(Album.photosdir, self.dirname, cover)

    @cached_property
    def photos(self):
        return [os.path.join(Album.photosdir, self.dirname, photo)
                for photo in os.listdir(self.path) if photo != COVER_FILENAME]

    @classmethod
    def all(cls):
        return [cls(dirname) for dirname in os.listdir(Album.photospath)]

    def __eq__(self, other):
        return self.date == other.date

    def __lt__(self, other):
        return self.date < other.date
