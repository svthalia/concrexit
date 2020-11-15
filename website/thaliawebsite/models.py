"""Custom models for Django OAuth2 Toolkit"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from oauth2_provider.models import AbstractApplication
from oauth2_provider.scopes import get_scopes_backend


class ScopedApplication(AbstractApplication):
    """
    Model that allows admins to set allowed scopes for an application
    """

    app_scopes = models.TextField(
        verbose_name=_("allowed scopes"),
        blank=True,
        help_text=_("Allowed scopes list, space separated"),
    )

    @property
    def allowed_scopes(self):
        """
        Returns the names of the scopes that this application is allowed to access
        """
        return set(get_scopes_backend().get_all_scopes().keys()) & set(
            str(self.app_scopes).split(" ")
        )
