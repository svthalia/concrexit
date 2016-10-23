"""
This module registers admin pages for the models
"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from utils.translation import TranslatedModelAdmin

from . import models

admin.site.register(models.Category)


@admin.register(models.Course)
class CourseAdmin(TranslatedModelAdmin):
    fields = ('name', 'shorthand', 'course_code', 'ec', 'since', 'until',
              'period', 'categories', 'old_courses')


@admin.register(models.Exam)
class ExamAdmin(TranslatedModelAdmin):
    list_display = ('type', 'course', 'exam_date', 'uploader',
                    'accepted')
    list_filter = ('accepted', 'exam_date', 'type')
    actions = ['accept', 'reject']

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark exams as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark exams as rejected")


@admin.register(models.Summary)
class SummaryAdmin(TranslatedModelAdmin):
    list_display = ('name', 'course', 'uploader', 'accepted')
    list_filter = ('accepted',)
    actions = ['accept', 'reject']

    def accept(self, request, queryset):
        queryset.update(accepted=True)

    accept.short_description = _("Mark summaries as accepted")

    def reject(self, request, queryset):
        queryset.update(accepted=False)

    reject.short_description = _("Mark summaries as rejected")
