from django.conf import settings
from django.core import validators
from django.db import models

from django.utils.translation import gettext_lazy as _


class ShortLink(models.Model):
    key = models.CharField(
        primary_key=True,
        max_length=32,
        validators=[validators.validate_slug],
        verbose_name=_("Name for the url"),
        help_text=_(f"This is what you use after https://{settings.SITE_DOMAIN}/"),
    )

    url = models.TextField(
        validators=[validators.URLValidator(schemes=["http", "https"])],
        verbose_name=_("Redirection target"),
        help_text=_("The url the user will be redirected to"),
    )

    immediate = models.BooleanField(
        default=False,
        verbose_name=_("Redirect without information page"),
        help_text=_(
            "Make sure to only do this when users expect an immediate redirect, if "
            "they expect a Thalia site a redirect will be confusing."
        ),
    )

    def __str__(self):
        return f"https://{settings.SITE_DOMAIN}/{self.key}"
