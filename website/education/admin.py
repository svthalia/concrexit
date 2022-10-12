"""This module registers admin pages for the models."""
import csv

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from . import models
from .forms import SummaryAdminForm

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


class WithDownloadCsv:
    def download_csv(self, request, queryset):
        opts = queryset.model._meta
        response = HttpResponse(content_type="text/csv")
        # force download.
        response["Content-Disposition"] = "attachment;filename=export.csv"
        # the csv writer
        writer = csv.writer(response)
        field_names = [field.name for field in opts.fields]
        # Write a first row with header information
        writer.writerow(field_names)
        # Write data rows
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    download_csv.short_description = _("Download marked as csv")


@admin.register(models.Exam)
class ExamAdmin(ObjectActionsMixin, ModelAdmin, WithDownloadCsv):
    list_display = (
        "type",
        "course",
        "exam_date",
        "uploader",
        "accepted",
        "language",
        "download_count",
    )
    readonly_fields = ("download_count", "accepted")
    list_filter = ("accepted", "exam_date", "type", "language")
    search_fields = (
        "name",
        "uploader__first_name",
        "uploader__last_name",
        "course__name",
    )
    actions = ["accept", "reject", "reset_download_count", "download_csv"]

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark exams as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark exams as rejected")

    def reset_download_count(self, request, queryset):
        queryset.update(download_count=0)

    reset_download_count.short_description = _("Reset the marked exams download count")

    @object_action(
        label=_("Accept"),
        parameter_name="_accept",
        permissions="education.change_exam",
        condition=lambda _, obj: not obj.accepted == True,
        log_message=_("Accepted"),
        perform_after_saving=True,
    )
    def accept_obj(self, request, obj):
        if obj:
            obj.accepted = True
            obj.save()
            return redirect("admin:education_exam_change", obj.pk)

    @object_action(
        label=_("Reject"),
        parameter_name="_reject",
        permissions="education.change_exam",
        condition=lambda _, obj: not obj.accepted or obj.accepted == True,
        log_message=_("Rejected"),
        perform_after_saving=True,
    )
    def reject_obj(self, request, obj):
        if obj:
            obj.accepted = False
            obj.save()
            return redirect("admin:education_exam_change", obj.pk)

    @object_action(
        label=_("Reset download count"),
        parameter_name="_resetdownloadcount",
        permissions="education.change_exam",
        condition=lambda _, obj: obj.download_count != 0,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Reset download count to 0"),
    )
    def reset_download_count_obj(self, request, obj):
        if obj:
            obj.download_count = 0
            obj.save()
            return redirect("admin:education_exam_change", obj.pk)

    object_actions_after_related_objects = ["reset_download_count_obj", "reject_obj", "accept_obj"]


@admin.register(models.Summary)
class SummaryAdmin(ObjectActionsMixin, ModelAdmin, WithDownloadCsv):
    list_display = (
        "name",
        "course",
        "uploader",
        "accepted",
        "language",
        "download_count",
    )
    readonly_fields = ("download_count", "accepted")
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
    @object_action(
        label=_("Accept"),
        parameter_name="_accept",
        permissions="education.change_summary",
        condition=lambda _, obj: not obj.accepted == True,
        log_message=_("Accepted"),
        perform_after_saving=True,
    )
    def accept_obj(self, request, obj):
        if obj:
            obj.accepted = True
            obj.save()
            return redirect("admin:education_summary_change", obj.pk)

    @object_action(
        label=_("Reject"),
        parameter_name="_reject",
        permissions="education.change_summary",
        condition=lambda _, obj: not obj.accepted or obj.accepted == True,
        log_message=_("Rejected"),
        perform_after_saving=True,
    )
    def reject_obj(self, request, obj):
        if obj:
            obj.accepted = False
            obj.save()
            return redirect("admin:education_summary_change", obj.pk)

    @object_action(
        label=_("Reset download count"),
        parameter_name="_resetdownloadcount",
        permissions="education.change_summary",
        condition=lambda _, obj: obj.download_count != 0,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Reset download count to 0"),
    )
    def reset_download_count_obj(self, request, obj):
        if obj:
            obj.download_count = 0
            obj.save()
            return redirect("admin:education_summary_change", obj.pk)

    object_actions_after_related_objects = ["reset_download_count_obj", "reject_obj", "accept_obj"]

