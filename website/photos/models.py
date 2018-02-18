import hashlib
import os
import random

from PIL.JpegImagePlugin import JpegImageFile
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from PIL import Image, ExifTags

from utils.translation import ModelTranslateMeta, MultilingualField

COVER_FILENAME = 'cover.jpg'

EXIF_ORIENTATION = {
    1: 0,
    2: 0,
    3: 180,
    4: 180,
    5: 90,
    6: 90,
    7: 270,
    8: 270,
}


def photo_uploadto(instance, filename):
    num = instance.album.photo_set.count()
    extension = os.path.splitext(filename)[1]
    new_filename = str(num).zfill(4) + extension
    return os.path.join(Album.photosdir, instance.album.dirname, new_filename)


def determine_rotation(pil_image):
    if isinstance(pil_image, JpegImageFile) and pil_image._getexif():
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in pil_image._getexif().items()
            if k in ExifTags.TAGS
        }
        if exif.get('Orientation'):
            return EXIF_ORIENTATION[exif.get('Orientation')]
    return 0


class Photo(models.Model):

    album = models.ForeignKey(
        'Album',
        on_delete=models.CASCADE,
        verbose_name=_("album")
    )

    file = models.ImageField(
        _('file'),
        upload_to=photo_uploadto
    )

    rotation = models.IntegerField(
        verbose_name=_('rotation'),
        default=0,
        choices=((x, x) for x in (0, 90, 180, 270)),
        help_text=_('This does not modify the original image file.'),
    )

    hidden = models.BooleanField(
        _('hidden'),
        default=False
    )

    _digest = models.CharField(
        'digest',
        max_length=40,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.file:
            self._orig_file = self.file.path
        else:
            self._orig_file = ""

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self._orig_file != self.file.path:
            image_path = self.file.path
            image = Image.open(image_path)

            self.rotation = determine_rotation(image)

            # Image.thumbnail does not upscale an image that is smaller
            image.thumbnail(settings.PHOTO_UPLOAD_SIZE, Image.ANTIALIAS)
            image.save(image_path, "JPEG")
            self._orig_file = self.file.path

            hash_sha1 = hashlib.sha1()
            for chunk in iter(lambda: self.file.read(4096), b""):
                hash_sha1.update(chunk)
            self.file.close()
            self._digest = hash_sha1.hexdigest()

            # Save again, to update changes in digest and rotation
            super().save(*args, **kwargs)

    class Meta:
        ordering = ('file', )


class Album(models.Model, metaclass=ModelTranslateMeta):
    title = MultilingualField(
        models.CharField,
        _("title"),
        max_length=200,
    )

    dirname = models.CharField(
        verbose_name=_('directory name'),
        max_length=200,
    )

    date = models.DateField(
        verbose_name=_('date'),
    )

    slug = models.SlugField(
        verbose_name=_('slug'),
        unique=True,
    )

    hidden = models.BooleanField(
        verbose_name=_('hidden'),
        default=False
    )

    _cover = models.OneToOneField(
        Photo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='covered_album',
        verbose_name=_('cover image'),
    )

    shareable = models.BooleanField(
        verbose_name=_('shareable'),
        default=False
    )

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
        super().save(*args, **kwargs)

    @property
    def access_token(self):
        return hashlib.sha256('{}album{}'.format(settings.SECRET_KEY, self.pk)
                              .encode('utf-8')).hexdigest()

    class Meta:
        ordering = ('-date', 'title_en')
