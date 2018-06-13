"""Registers admin interfaces for the documents module"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from documents.forms import AnnualDocumentForm, GeneralMeetingForm
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


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the memberships on those started or ended in a lecture year"""
    title = _('lecture year')
    parameter_name = 'lecture_year'

    def lookups(self, request, model_admin):
        if AnnualDocument.objects.count() > 0:
            first_year = AnnualDocument.objects.order_by('year').first().year
            last_year = AnnualDocument.objects.order_by('year').last().year

            return [(year, '{}-{}'.format(year, year+1))
                    for year in range(last_year, first_year-1, -1)]
        return []

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())

        return queryset.filter(year=year)


@admin.register(AnnualDocument)
class AnnualDocumentAdmin(TranslatedModelAdmin):
    """Manage the annual documents"""
    form = AnnualDocumentForm
    fields = ('file', 'subcategory', 'year', 'members_only',)
    list_filter = (LectureYearFilter, 'created', 'last_updated',)


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
