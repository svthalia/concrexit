"""The admin interfaces registered by the mailinglists package."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ListAlias, MailingList, VerbatimAddress


class VerbatimAddressInline(admin.TabularInline):
    """Class to inline show the VerbatimAddress."""

    model = VerbatimAddress


class ListAliasInline(admin.TabularInline):
    """Class to inline show the ListAlias."""

    model = ListAlias


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    """Class to show the mailing lists in the admin."""

    filter_horizontal = ("members",)
    inlines = (VerbatimAddressInline, ListAliasInline)
    list_display = ("name", "alias_names", "moderated", "description")
    readonly_fields = ("active_gsuite_name",)
    search_fields = ["name", "aliases__alias"]

    def alias_names(self, obj):
        """Return list of aliases of obj."""
        return [x.alias for x in obj.aliases.all()]

    alias_names.short_description = _("List aliases")
