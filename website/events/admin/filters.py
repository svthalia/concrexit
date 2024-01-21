from datetime import date

from django.contrib import admin
from django.db.models import Max, Min
from django.utils.translation import gettext_lazy as _

from utils.snippets import datetime_to_lectureyear


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the events on those started or ended in a lecture year."""

    title = _("lecture year")
    parameter_name = "lecture_year"

    def lookups(self, request, model_admin):
        objects_end = model_admin.model.objects.aggregate(Max("end"))
        objects_start = model_admin.model.objects.aggregate(Min("start"))

        if objects_end["end__max"] and objects_start["start__min"]:
            year_end = datetime_to_lectureyear(objects_end["end__max"])
            year_start = datetime_to_lectureyear(objects_start["start__min"])

            return [
                (year, f"{year}-{year + 1}")
                for year in range(year_end, year_start - 1, -1)
            ]
        return []

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())
        year_start = date(year=year, month=9, day=1)
        year_end = date(year=year + 1, month=9, day=1)

        return queryset.filter(start__gte=year_start, end__lte=year_end)
