from django.contrib import admin

from .models import MailingList, VerbatimAddress, ListAlias


class VerbatimAddressInline(admin.TabularInline):
    model = VerbatimAddress


class ListAliasInline(admin.TabularInline):
    model = ListAlias


@admin.register(MailingList)
class GeneralMeetingAdmin(admin.ModelAdmin):
    inlines = (VerbatimAddressInline, ListAliasInline)
