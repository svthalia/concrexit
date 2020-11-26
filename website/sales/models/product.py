from django.db import models


class Product(models.Model):
    """Products that can be ordered."""

    name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    age_restricted = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.name


    class Meta:
        """Meta class."""
        ordering = ["name"]
