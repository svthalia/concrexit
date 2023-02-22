from django.db import models
from django.utils.translation import gettext_lazy as _

from moneybird.models import SynchronizableMoneybirdResourceModel

class Contact(SynchronizableMoneybirdResourceModel):
    first_name = models.CharField(
        verbose_name=_("first name"),
        max_length=255,
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name=_("last name"),
        max_length=255,
        null=True,
        blank=True,
    )
    address_1 = models.CharField(
        verbose_name=_("address 1"),
        max_length=255,
        null=True,
        blank=True,
    )
    address_2 = models.CharField(
        verbose_name=_("address 2"),
        max_length=255,
        null=True,
        blank=True,
    )
    zipcode = models.CharField(
        verbose_name=_("zipcode"),
        max_length=255,
        null=True,
        blank=True,
    )
    city = models.CharField(
        verbose_name=_("city"),
        max_length=255,
        null=True,
        blank=True,
    )
    country = models.CharField(
        verbose_name=_("country"),
        max_length=255,
        null=True,
        blank=True,
    )
    email = models.EmailField(
        verbose_name=_("email"),
        null=True,
        blank=True,
    )

