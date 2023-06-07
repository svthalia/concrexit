"""Registers admin interfaces for the documents module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

from documents import forms
from documents.models import (
    AnnualDocument,
    AssociationDocument,
    GeneralMeeting,
    Minutes,
    MiscellaneousDocument,
)


class MinutesInline(admin.StackedInline):
    """Inline for minutes of a general meeting."""

    model = Minutes
    form = forms.MinutesForm
    extra = 0


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(ModelAdmin):
    """Manage the general meetings."""

    form = forms.GeneralMeetingForm
    inlines = [
        MinutesInline,
    ]
    list_filter = ("datetime",)


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the memberships on those started or ended in a lecture year."""

    title = _("lecture year")
    parameter_name = "lecture_year"

    def lookups(self, request, model_admin):
        if AnnualDocument.objects.exists():
            first_year = AnnualDocument.objects.order_by("year").first().year
            last_year = AnnualDocument.objects.order_by("year").last().year

            return [
                (year, f"{year}-{year + 1}")
                for year in range(last_year, first_year - 1, -1)
            ]
        return []

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())

        return queryset.filter(year=year)


@admin.register(AnnualDocument)
class AnnualDocumentAdmin(ModelAdmin):
    """Manage the annual documents."""

    form = forms.AnnualDocumentForm
    list_filter = (
        LectureYearFilter,
        "created",
        "last_updated",
        "members_only",
    )
    list_display = (
        "__str__",
        "members_only",
    )


@admin.register(AssociationDocument)
class AssociationDocumentAdmin(ModelAdmin):
    """Manage the association documents."""

    form = forms.AssociationDocumentForm
    list_filter = (
        "created",
        "last_updated",
        "members_only",
    )
    list_display = (
        "__str__",
        "members_only",
    )


@admin.register(MiscellaneousDocument)
class MiscellaneousDocumentAdmin(ModelAdmin):
    """Manage the miscellaneous documents."""

    form = forms.MiscellaneousDocumentForm
    list_filter = (
        "created",
        "last_updated",
        "members_only",
    )
    list_display = (
        "__str__",
        "members_only",
    )
