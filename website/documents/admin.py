"""Registers admin interfaces for the documents module"""
from django.contrib import admin

from documents.forms import GeneralMeetingForm
from documents.models import (AnnualDocument, AssociationDocument,
                              GeneralMeeting, Minutes,
                              MiscellaneousDocument)
from utils.translation import TranslatedModelAdmin


class MinutesInline(admin.StackedInline):
    """Inline for minutes of a general meeting"""
    model = Minutes
    fields = ('file_nl', 'file_en', 'members_only',)


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(TranslatedModelAdmin):
    """Manage the general meetings"""
    form = GeneralMeetingForm
    inlines = [
        MinutesInline,
    ]
    list_filter = ('datetime',)


@admin.register(AnnualDocument)
class AnnualDocument(TranslatedModelAdmin):
    """Manage the annual documents"""
    fields = ('file', 'subcategory', 'year', 'members_only',)
    list_filter = ('year', 'created', 'last_updated',)


@admin.register(AssociationDocument)
class AssociationDocumentAdmin(TranslatedModelAdmin):
    """Manage the association documents"""
    fields = ('name', 'file', 'members_only',)
    list_filter = ('created', 'last_updated',)


@admin.register(MiscellaneousDocument)
class MiscellaneousDocumentAdmin(TranslatedModelAdmin):
    """Manage the miscellaneous documents"""
    fields = ('name', 'file', 'members_only',)
    list_filter = ('created', 'last_updated',)
