"""This module registers admin pages for the models."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

from import_export.admin import ExportActionMixin

from . import models
from .forms import SummaryAdminForm
from .resources import ExamResource, SummaryResource

admin.site.register(models.Category)


@admin.register(models.Course)
class CourseAdmin(ModelAdmin):
    fields = (
        "name",
        "course_code",
        "ec",
        "since",
        "until",
        "categories",
        "old_courses",
    )
    list_filter = ("categories", "ec")
    search_fields = ("name", "course_code")


@admin.register(models.Exam)
class ExamAdmin(ExportActionMixin, ModelAdmin):
    resource_classes = (ExamResource,)
    list_display = (
        "type",
        "course",
        "exam_date",
        "uploader",
        "accepted",
        "language",
        "download_count",
    )
    readonly_fields = ("download_count",)
    list_filter = ("accepted", "exam_date", "type", "language")
    search_fields = (
        "name",
        "uploader__first_name",
        "uploader__last_name",
        "course__name",
    )
    actions = ["accept", "reject", "reset_download_count"]

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark exams as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark exams as rejected")

    def reset_download_count(self, request, queryset):
        queryset.update(download_count=0)

    reset_download_count.short_description = _("Reset the marked exams download count")


@admin.register(models.Summary)
class SummaryAdmin(ExportActionMixin, ModelAdmin):
    resource_classes = (SummaryResource,)
    list_display = (
        "name",
        "course",
        "uploader",
        "accepted",
        "language",
        "download_count",
    )
    readonly_fields = ("download_count",)
    list_filter = ("accepted", "language")
    search_fields = (
        "name",
        "uploader__first_name",
        "uploader__last_name",
        "course__name",
    )
    actions = ["accept", "reject", "reset_download_count", "download_csv"]
    form = SummaryAdminForm

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark summaries as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark summaries as rejected")

    def reset_download_count(self, request, queryset):
        queryset.update(download_count=0)

    reset_download_count.short_description = _(
        "Reset the marked summaries download count"
    )
