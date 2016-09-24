from django.urls import reverse
from django.conf import settings
from django.utils.functional import cached_property
from django.db import models

from PIL import Image

import hashlib
import os
import random

COVER_FILENAME = 'cover.jpg'


def photo_uploadto(instance, filename):
    return os.path.join(Album.photosdir, instance.album.dirname, filename)


class Photo(models.Model):
    album = models.ForeignKey('Album', on_delete=models.CASCADE)
    file = models.ImageField(upload_to=photo_uploadto)
    rotation = models.IntegerField(
        default=0,
        choices=((x, x) for x in (0, 90, 180, 270)),
        help_text="This does not modify the original image file.",
    )
    hidden = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.file:
            self._orig_file = self.file.path
        else:
            self._orig_file = ""

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        super(Photo, self).save(*args, **kwargs)

        if self._orig_file != self.file.path:
            image_path = self.file.path
            image = Image.open(image_path)
            # Image.thumbnail does not upscale an image that is smaller
            image.thumbnail(settings.PHOTO_UPLOAD_SIZE, Image.ANTIALIAS)
            image.save(image_path, "JPEG")
            self._orig_file = self.file.path


class Album(models.Model):
    title = models.CharField(max_length=200)
    dirname = models.CharField(max_length=200)
    date = models.DateField()
    slug = models.SlugField()
    hidden = models.BooleanField(default=False)
    _cover = models.OneToOneField(Photo, on_delete=models.SET_NULL, blank=True,
                                  null=True, related_name='covered_album')
    shareable = models.BooleanField(default=False)

    photosdir = 'photos'
    photospath = os.path.join(settings.MEDIA_ROOT, photosdir)

    @cached_property
    def cover(self):
        if self._cover is not None:
            return self._cover
        else:
            random.seed(self.dirname)
            cover = random.choice(self.photo_set.all())
        return cover

    def __str__(self):
        return '{} {}'.format(self.date.strftime('%Y-%m-%d'), self.title)

    def get_absolute_url(self):
        return reverse('photos:album', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        # dirname is only set for new objects, to avoid ever changing it
        if self.pk is None:
            self.dirname = self.slug
        super(Album, self).save(*args, **kwargs)

    @property
    def access_token(self):
        return hashlib.sha256('{}album{}'.format(settings.SECRET_KEY, self.pk)
                              .encode('utf-8')).hexdigest()
