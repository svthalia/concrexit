"""Models for the merchandise database tables"""
from django.db import models

from utils.translation import ModelTranslateMeta, MultilingualField


class MerchandiseItem(models.Model, metaclass=ModelTranslateMeta):
    """
    Merchandise items

    This model describes merchandise items.
    """

    #: Name of the merchandise item.
    name = MultilingualField(models.CharField, max_length=200)

    #: Price of the merchandise item
    price = models.DecimalField(max_digits=5, decimal_places=2)

    #: Description of the merchandise item
    description = MultilingualField(models.TextField)

    #: Image of the merchandise item
    image = models.ImageField(upload_to="public/merchandise")

    def __str__(self):
        """Gives the name of the merchandise item in the currently
        active locale.

        :return: The name of the merchandise item.
        :rtype: str
        """
        return self.name
