"""Settings for the admin site."""

from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_otp import user_has_device


class ThaliaAdminSite(admin.AdminSite):
    site_header = _("Thalia administration")
    site_title = _("Thalia")

    def has_permission(self, request):
        return super().has_permission(request) and (
            not settings.ADMIN_REQUIRE_2FA or user_has_device(request.user)
        )
