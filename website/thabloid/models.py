import os
import shutil
import subprocess
from itertools import zip_longest

from PIL import Image
from django.conf import settings
from django.core.files import temp
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from utils.media.services import save_image
from utils.threading import PopenAndCall


def thabloid_filename(instance, filename):
    """Return path of thabloid."""
    ext = os.path.splitext(filename)[1]
    return os.path.join("thabloids/", slugify(instance) + ext)


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
        if self.file.storage.exists(os.path.dirname(self.page_url())):
            pages = self.file.storage.listdir(os.path.dirname(self.page_url()))[1]
            count = len(pages) * 2 - 1
            return map(lambda p: self.page_url(p[0], p[1]), pagesets(count))
        return []

    def get_absolute_url(self):
        """Get url of Thabloid."""
        return reverse(
            "thabloid:pages", kwargs={"year": self.year, "issue": self.issue}
        )

    def post_extract(self):
        """Save extracted pages to disk."""
        dir_name = os.path.dirname(os.path.join(temp.gettempdir(), self.page_url()))
        pages = os.listdir(
            dir_name
        )
        pages = sorted(pages)

        first_page = Image.open(os.path.join(dir_name, pages[0]))
        save_image(self.file.storage, first_page, self.page_url(1), "PNG")
        last_page = Image.open(os.path.join(dir_name, pages[-1]))
        save_image(self.file.storage, last_page, self.page_url(len(pages)), "PNG")

        pages = pages[1:-1]
        count = int(len(pages) / 2)

        for i in range(0, count):
            i = i * 2
            spread_left = os.path.join(dir_name, pages[i])
            spread_right = os.path.join(dir_name, pages[i + 1])

            result = Image.new("RGB", (2100, 1485))

            img_left = Image.open(spread_left)
            result.paste(img_left, (0, 0, 1050, 1485))
            img_right = Image.open(spread_right)
            result.paste(img_right, (1050, 0, 2100, 1485))

            save_image(self.file.storage, result, self.page_url(i + 2, i + 3), "PNG")

            os.remove(spread_left)
            os.remove(spread_right)

    def extract_thabloid_pages(self, wait):
        """Extract the pages of a Thabloid using Ghostscript."""
        dst = os.path.join(temp.gettempdir(), self.page_url())
        src = os.path.join(temp.gettempdir(), self.file.name)

        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as f:
            f.write(self.file.read())
            f.close()

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

            if self.file != old.file:
                new_file = True

            elif self.year != old.year or self.issue != old.issue:
                self.file.name = thabloid_filename(self, self.file.name)

                for old_page in old.pages:
                    new_page = old_page.replace(os.path.splitext(os.path.basename(old.file.name))[0], os.path.splitext(os.path.basename(self.file.name))[0])
                    old.file.storage.rename(old_page, new_page)
                old.file.storage.rename(old.file.name, self.file.name)

            if new_file:
                for page in old.pages:
                    old.file.storage.delete(page)
                old.file.storage.delete(old.file.name)

        super().save(*args, **kwargs)

        if new_file:
            self.extract_thabloid_pages(wait)
