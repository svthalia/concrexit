"""The admin interfaces registered by the mailinglists package"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

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

    filter_horizontal = ('members',)
    inlines = (VerbatimAddressInline, ListAliasInline)
    list_display = ('name', 'alias_names', 'description')
    search_fields = ['name', 'prefix', 'aliasses__alias']

    def alias_names(self, obj):
        """Return list of aliases of obj."""
        return [x.alias for x in obj.aliasses.all()]
    alias_names.short_description = _('List aliasses')
