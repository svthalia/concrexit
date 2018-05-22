"""
This module registers admin pages for the models
"""
import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from utils.translation import TranslatedModelAdmin

from . import models

admin.site.register(models.Category)


@admin.register(models.Course)
class CourseAdmin(TranslatedModelAdmin):
    fields = ('name', 'shorthand', 'course_code', 'ec', 'since', 'until',
              'period', 'categories', 'old_courses')
    list_filter = ('categories', 'ec')
    search_fields = ('name', 'course_code')


@admin.register(models.Exam)
class ExamAdmin(TranslatedModelAdmin):
    list_display = ('type', 'course', 'exam_date', 'uploader',
                    'accepted', 'download_count')
    readonly_fields = ('download_count',)
    list_filter = ('accepted', 'exam_date', 'type',)
    search_fields = ('name', 'uploader__first_name', 'uploader__last_name',
                     'course__name_nl', 'course__name_en',)
    actions = ['accept', 'reject', 'reset_download_count', 'download_csv']

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark exams as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark exams as rejected")

    def reset_download_count(self, request, queryset):
        queryset.update(download_count=0)

    reset_download_count.short_description = _("Reset the marked exams "
                                               "download count")

    def download_csv(self, request, queryset):
        opts = queryset.model._meta
        response = HttpResponse(content_type='text/csv')
        # force download.
        response['Content-Disposition'] = 'attachment;filename=export.csv'
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


@admin.register(models.Summary)
class SummaryAdmin(TranslatedModelAdmin):
    list_display = ('name', 'course', 'uploader', 'accepted', 'download_count')
    readonly_fields = ('download_count',)
    list_filter = ('accepted',)
    search_fields = ('name', 'uploader__first_name', 'uploader__last_name',
                     'course__name_nl', 'course__name_en',)
    actions = ['accept', 'reject', 'reset_download_count', 'download_csv']

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark summaries as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark summaries as rejected")

    def reset_download_count(self, request, queryset):
        queryset.update(download_count=0)

    reset_download_count.short_description = _("Reset the marked summaries "
                                               "download count")

    def download_csv(self, request, queryset):
        opts = queryset.model._meta
        response = HttpResponse(content_type='text/csv')
        # force download.
        response['Content-Disposition'] = 'attachment;filename=export.csv'
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
