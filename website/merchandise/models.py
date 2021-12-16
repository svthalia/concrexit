"""Models for the merchandise database tables."""
from django.db import models

from payments.models import PaymentAmountField


class MerchandiseItem(models.Model):
    """Merchandise items.

    This model describes merchandise items.
    """

    #: Name of the merchandise item.
    name = models.CharField(max_length=200)

    #: Price of the merchandise item
    price = PaymentAmountField()

    #: Description of the merchandise item
    description = models.TextField()

    #: Image of the merchandise item
    image = models.ImageField(upload_to="public/merchandise")

    def __str__(self):
        """Give the name of the merchandise item in the currently active locale.

        :return: The name of the merchandise item.
        :rtype: str
        """
        return str(self.name)
