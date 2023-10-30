"""Models for the merchandise database tables."""
from django.core.files.storage import storages
from django.db import models

from thumbnails.fields import ImageField

from utils.media.services import get_upload_to_function

_merchandise_photo_upload_to = get_upload_to_function("merchandise")


class MerchandiseItem(models.Model):
    """Merchandise items.

    This model describes merchandise items.
    """

    #: Name of the merchandise item.
    name = models.CharField(max_length=200)

    #: Price of the merchandise item
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    #: Description of the merchandise item
    description = models.TextField()

    #: Image of the merchandise item
    image = ImageField(
        upload_to=_merchandise_photo_upload_to,
        storage=storages["public"],
        resize_source_to="source",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.image:
            self._orig_image = self.image.name
        else:
            self._orig_image = None

    def delete(self, using=None, keep_parents=False):
        if self.image.name:
            self.image.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        super().save(**kwargs)
        storage = self.image.storage

        if self._orig_image and self._orig_image != self.image.name:
            storage.delete(self._orig_image)
            self._orig_image = None

    def __str__(self):
        """Give the name of the merchandise item in the currently active locale.

        :return: The name of the merchandise item.
        :rtype: str
        """
        return str(self.name)
