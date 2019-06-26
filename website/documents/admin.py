"""Registers admin interfaces for the documents module"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from documents import forms
from documents.models import (AnnualDocument, AssociationDocument,
                              EventDocument, GeneralMeeting, Minutes,
                              MiscellaneousDocument)
from documents.services import is_owner
from utils.translation import TranslatedModelAdmin


class MinutesInline(admin.StackedInline):
    """Inline for minutes of a general meeting"""
    model = Minutes
    form = forms.MinutesForm
    extra = 0


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(TranslatedModelAdmin):
    """Manage the general meetings"""
    form = forms.GeneralMeetingForm
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
    form = forms.AnnualDocumentForm
    list_filter = (LectureYearFilter, 'created', 'last_updated',)


@admin.register(AssociationDocument)
class AssociationDocumentAdmin(TranslatedModelAdmin):
    """Manage the association documents"""
    form = forms.AssociationDocumentForm
    list_filter = ('created', 'last_updated',)


@admin.register(EventDocument)
class EventDocumentAdmin(TranslatedModelAdmin):
    """Manage the event documents"""
    form = forms.EventDocumentForm
    list_filter = ('created', 'last_updated',)

    def has_change_permission(self, request, document=None):
        """Only allow access to the change form if the user is an owner"""
        if (document is not None and
                not is_owner(request.member, document)):
            return False
        return super().has_change_permission(request, document)

    def has_delete_permission(self, request, document=None):
        """Only allow delete access if the user is an owner"""
        if (document is not None and
                not is_owner(request.member, document)):
            return False
        return super().has_delete_permission(request, document)


@admin.register(MiscellaneousDocument)
class MiscellaneousDocumentAdmin(TranslatedModelAdmin):
    """Manage the miscellaneous documents"""
    form = forms.MiscellaneousDocumentForm
    list_filter = ('created', 'last_updated',)
