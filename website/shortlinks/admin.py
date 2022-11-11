from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ShortLink


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["slug"].help_text = _(
            f"This is what you use after https://{settings.SITE_DOMAIN}/"
        )
        return form
