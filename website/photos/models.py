from django.urls import reverse
from django.conf import settings
from django.utils.functional import cached_property
from django.db import models

import os
import random

COVER_FILENAME = 'cover.jpg'


class Album(models.Model):
    title = models.CharField(max_length=200)
    dirname = models.CharField(max_length=200)
    date = models.DateField()
    slug = models.SlugField()

    photosdir = 'photos'
    photospath = os.path.join(settings.MEDIA_ROOT, photosdir)

    @property
    def path(self):
        return os.path.join(Album.photospath, self.dirname)

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

    def __str__(self):
        return '{} {}'.format(self.date.strftime('%Y-%m-%d'), self.title)

    def get_absolute_url(self):
        return reverse('photos:album', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        # dirname is only set for new objects, to avoid ever changing it
        if self.pk is None:
            self.dirname = self.slug
        super(Album, self).save(*args, **kwargs)
