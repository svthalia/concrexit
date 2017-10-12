from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import ListAlias, MailingList, VerbatimAddress


class VerbatimAddressInline(admin.TabularInline):
    model = VerbatimAddress


class ListAliasInline(admin.TabularInline):
    model = ListAlias


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    inlines = (VerbatimAddressInline, ListAliasInline)
    list_display = ('name', 'alias_names',)
    search_fields = ['name', 'prefix', 'aliasses__alias']

    def alias_names(self, obj):
        return [x.alias for x in obj.aliasses.all()]
    alias_names.short_description = _('List aliasses')
