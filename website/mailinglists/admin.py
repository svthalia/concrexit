from django.contrib import admin

from .models import ListAlias, MailingList, VerbatimAddress


class VerbatimAddressInline(admin.TabularInline):
    model = VerbatimAddress


class ListAliasInline(admin.TabularInline):
    model = ListAlias


@admin.register(MailingList)
class GeneralMeetingAdmin(admin.ModelAdmin):
    inlines = (VerbatimAddressInline, ListAliasInline)
