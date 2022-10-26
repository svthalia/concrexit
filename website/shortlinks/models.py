from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ShortLink(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=32,
        verbose_name=_("name for the url"),
        help_text=_(
            "This is what you use after the root domain. Be mindful that the url "
            "this creates could be overridden by a website update."
        ),
    )

    url = models.URLField(
        verbose_name=_("redirection target"),
        help_text=_("The url the user will be redirected to."),
    )

    immediate = models.BooleanField(
        default=False,
        verbose_name=_("redirect without information page"),
        help_text=_(
            "Make sure to only do this when users expect an immediate redirect, if "
            "they expect a Thalia site a redirect will be confusing."
        ),
    )

    def __str__(self):
        return f"https://{settings.SITE_DOMAIN}/{self.slug}"
