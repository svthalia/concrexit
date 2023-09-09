import os
from itertools import zip_longest

from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from thumbnails.fields import ImageField


def thabloid_filename(instance, filename):
    """Return path of thabloid."""
    ext = os.path.splitext(filename)[1]
    return os.path.join("thabloids/", slugify(instance) + ext)


def thabloid_cover_filename(instance, filename):
    """Return path of thabloid cover."""
    ext = os.path.splitext(filename)[1]
    return os.path.join("thabloids/covers/", slugify(instance) + ext)


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
        validators=[FileExtensionValidator(["pdf"])],
    )

    cover = ImageField(upload_to=thabloid_cover_filename, resize_source_to="source")

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

    def get_absolute_url(self):
        """Get url of Thabloid."""
        return reverse(
            "thabloid:detail", kwargs={"year": self.year, "issue": self.issue}
        )
