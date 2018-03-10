import os
import shutil
import subprocess

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from utils.validators import validate_file_extension


def thabloid_filename(instance, filename):
    ext = os.path.splitext(filename)[1]
    return os.path.join('public/thabloids/', slugify(instance) + ext)


class Thabloid(models.Model):
    year = models.IntegerField(
        verbose_name='academic year',
        validators=[MinValueValidator(1990)]
    )

    issue = models.IntegerField()

    file = models.FileField(
        upload_to=thabloid_filename,
        validators=[validate_file_extension],
    )

    class Meta:
        unique_together = ('year', 'issue',)
        ordering = ('-year', '-issue')

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
        return reverse('thabloid:pages', kwargs={'year': self.year,
                                                 'issue': self.issue})

    def extract_thabloid_pages(self, wait):
        dst = os.path.join(settings.MEDIA_ROOT, self.page_url())
        name = thabloid_filename(self, self.file.name)
        src = os.path.join(settings.MEDIA_ROOT, name)

        try:
            # Remove potential remainders
            shutil.rmtree(os.path.dirname(dst))
        except FileNotFoundError:
            pass

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # TODO reconsider if this resolution / quality is sufficient
        p = subprocess.Popen(['gs', '-o', dst,
                              # '-g2100x2970', '-dPDFFitPage',
                              '-g1050x1485', '-dPDFFitPage',
                              '-sDEVICE=jpeg', '-f', src],
                             stdout=subprocess.DEVNULL
                             )
        if wait:  # pragma: no cover
            p.wait()

    def save(self, *args, wait=False, **kwargs):
        new_file = False

        if self.pk is None:
            new_file = True
        else:
            old = Thabloid.objects.get(pk=self.pk)
            old_dir = os.path.join(settings.MEDIA_ROOT, old.page_url())
            old_dir = os.path.dirname(old_dir)

            if self.file != old.file:
                new_file = True

            elif self.year != old.year or self.issue != old.issue:
                self.file.name = thabloid_filename(self, self.file.name)

                new_dir = os.path.join(settings.MEDIA_ROOT, self.page_url())
                new_dir = os.path.dirname(new_dir)
                try:
                    shutil.rmtree(new_dir)
                except FileNotFoundError:
                    pass

                os.rename(old_dir, new_dir)
                os.rename(os.path.join(settings.MEDIA_ROOT, old.file.name),
                          os.path.join(settings.MEDIA_ROOT, self.file.name))

        if new_file:
            filename = thabloid_filename(self, self.file.name)
            src = os.path.join(settings.MEDIA_ROOT, filename)

            # Removes the .pdf file if it already exists
            try:
                os.remove(src)
            except FileNotFoundError:
                pass

        super(Thabloid, self).save(*args, **kwargs)

        if new_file:
            self.extract_thabloid_pages(wait)
