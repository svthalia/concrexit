from django.contrib import admin
from members.models import Member

from .models import ListAlias, MailingList, VerbatimAddress


class VerbatimAddressInline(admin.TabularInline):
    model = VerbatimAddress


class ListAliasInline(admin.TabularInline):
    model = ListAlias


@admin.register(MailingList)
class GeneralMeetingAdmin(admin.ModelAdmin):
    model = Member
    filter_horizontal = ('members',)
    inlines = (VerbatimAddressInline, ListAliasInline)
