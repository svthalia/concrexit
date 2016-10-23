from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.urls import reverse

from utils.validators import validate_file_extension

import os
import subprocess
import shutil


def thabloid_filename(instance, filename):
    ext = os.path.splitext(filename)[1]
    return os.path.join('public/thabloids/', slugify(instance) + ext)


class Thabloid(models.Model):
    year = models.IntegerField(validators=[MinValueValidator(1990)])
    issue = models.IntegerField()
    file = models.FileField(
        upload_to=thabloid_filename,
        validators=[validate_file_extension],
    )

    class Meta:
        unique_together = ('year', 'issue',)

    def __str__(self):
        return 'Thabloid {}-{}, #{}'.format(self.year, self.year+1, self.issue)

    def page_url(self, page=None):
        if page is None:
            page = '%03d.jpg'
        else:
            page = '{:03}.jpg'.format(page)
        dst, ext = os.path.splitext(self.file.name)
        return os.path.join(os.path.dirname(dst), 'pages',
                            os.path.basename(dst), page)

    @property
    def cover(self):
        return self.page_url(1)

    @property
    def pages(self):
        pages = os.listdir(os.path.join(settings.MEDIA_ROOT,
                           os.path.dirname(self.page_url())))
        return [self.page_url(i+1) for i in range(len(pages))]

    def get_absolute_url(self):
        return reverse('viewer', kwargs={'year': self.year,
                                         'issue': self.issue})

    def save(self, *args, **kwargs):
        super(Thabloid, self).save(*args, **kwargs)
        src = self.file.path

        # For overwriting already existing files
        new_name = thabloid_filename(self, self.file.name)
        new_src = os.path.join(settings.MEDIA_ROOT, new_name)
        if src != new_src:
            os.rename(src, new_src)
            src = new_src
            self.file.name = new_name
            self.save()

        dst = os.path.join(settings.MEDIA_ROOT, self.page_url())

        try:
            shutil.rmtree(os.path.dirname(dst))  # Remove potential remainders
        except FileNotFoundError:
            pass
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # TODO reconsider if this resolution / quality is sufficient
        subprocess.Popen(['gs', '-o', dst,
                          # '-g2100x2970', '-dPDFFitPage',
                          '-g1050x1485', '-dPDFFitPage',
                          '-sDEVICE=jpeg', '-f', src])
