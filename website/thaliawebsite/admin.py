"""Settings for the admin site."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("Thalia administration")
admin.site.site_title = _("Thalia")
