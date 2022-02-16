import os
import shutil
import subprocess
from itertools import zip_longest

from PIL import Image
from django.conf import settings
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from utils.threading import PopenAndCall


def thabloid_filename(instance, filename):
    """Return path of thabloid."""
    ext = os.path.splitext(filename)[1]
    return os.path.join("private/thabloids/", slugify(instance) + ext)


def pagesets(count):
    if count < 1:
        return []
    pageiter = iter(range(2, count))
    return [(1, None)] + list(zip_longest(pageiter, pageiter))


class Thabloid(models.Model):
    """Model representing a Thabloid."""

    year = models.IntegerField(
        verbose_name="academic year", validators=[MinValueValidator(1990)]
    )

    issue = models.IntegerField()

    file = models.FileField(
        upload_to=thabloid_filename,
        validators=[FileExtensionValidator(["txt", "pdf", "jpg", "jpeg", "png"])],
    )

    class Meta:
        """Meta class for Thabloid model."""

        unique_together = (
            "year",
            "issue",
        )
        ordering = ("-year", "-issue")

    def __str__(self):
        """Return string representation of a Thabloid object."""
        return f"Thabloid {self.year}-{self.year + 1}, #{self.issue}"

    def page_url(self, page=None, second_page=None):
        """Return path of Thabloid pages image."""
        if page is None:
            page = "%03d.png"
        elif second_page is None:
            page = f"{page:03}.png"
        else:
            page = f"{page:03}-{second_page:03}.png"
        dst, _ = os.path.splitext(self.file.name)
        return os.path.join(os.path.dirname(dst), "pages", os.path.basename(dst), page)

    @property
    def cover(self):
        """Return first page as cover."""
        return self.page_url(1)

    def pagesets(self, count):
        """Return list of pages to should be shown together."""
        if count < 1:
            return []
        pageiter = iter(range(2, count))
        return [(1, None)] + list(zip_longest(pageiter, pageiter))

    @property
    def pages(self):
        """Return urls of pages that should be shown together."""
        pages = os.listdir(
            os.path.join(settings.MEDIA_ROOT, os.path.dirname(self.page_url()))
        )
        count = len(pages) * 2 - 1
        return map(lambda p: self.page_url(p[0], p[1]), pagesets(count))

    def get_absolute_url(self):
        """Get url of Thabloid."""
        return reverse(
            "thabloid:pages", kwargs={"year": self.year, "issue": self.issue}
        )

    def post_extract(self):
        """Save extracted pages to disk."""
        pages = os.listdir(
            os.path.join(settings.MEDIA_ROOT, os.path.dirname(self.page_url()))
        )
        pages = [self.page_url(i + 1) for i in range(len(pages))]
        pages = sorted(pages)
        pages = pages[1:-1]
        count = int(len(pages) / 2)
        dirname = os.path.join(settings.MEDIA_ROOT, os.path.dirname(self.page_url()))

        for i in range(0, count):
            i = i * 2
            spread_left = os.path.join(settings.MEDIA_ROOT, pages[i])
            spread_right = os.path.join(settings.MEDIA_ROOT, pages[i + 1])

            result = Image.new("RGB", (2100, 1485))

            img_left = Image.open(spread_left)
            result.paste(img_left, (0, 0, 1050, 1485))
            img_right = Image.open(spread_right)
            result.paste(img_right, (1050, 0, 2100, 1485))

            filename = (
                os.path.splitext(os.path.basename(spread_left))[0]
                + "-"
                + os.path.splitext(os.path.basename(spread_right))[0]
                + ".png"
            )
            result.save(os.path.join(dirname, filename), "PNG")

            os.remove(spread_left)
            os.remove(spread_right)

    def extract_thabloid_pages(self, wait):
        """Extract the pages of a Thabloid using Ghostscript."""
        dst = os.path.join(settings.MEDIA_ROOT, self.page_url())
        name = thabloid_filename(self, self.file.name)
        src = os.path.join(settings.MEDIA_ROOT, name)

        try:
            # Remove potential remainders
            shutil.rmtree(os.path.dirname(dst))
        except FileNotFoundError:
            pass

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        thread = PopenAndCall(
            self.post_extract,
            [
                "gs",
                "-o",
                dst,
                "-g1050x1485",
                "-dPDFFitPage",
                "-dTextAlphaBits=4",
                "-sDEVICE=png16m",
                "-f",
                src,
            ],
            stdout=subprocess.DEVNULL,
        )
        if wait:
            thread.join()

    def save(self, *args, wait=False, **kwargs):
        """Save Thabloid to disk."""
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
                os.rename(
                    os.path.join(settings.MEDIA_ROOT, old.file.name),
                    os.path.join(settings.MEDIA_ROOT, self.file.name),
                )

        if new_file:
            filename = thabloid_filename(self, self.file.name)
            src = os.path.join(settings.MEDIA_ROOT, filename)

            # Removes the .pdf file if it already exists
            try:
                os.remove(src)
            except FileNotFoundError:
                pass

        super().save(*args, **kwargs)

        if new_file:
            self.extract_thabloid_pages(wait)
