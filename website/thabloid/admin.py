from django import forms
from django.contrib import admin
from django.utils import timezone

from thabloid.models import Thabloid
from utils.snippets import datetime_to_lectureyear


def association_year_choices():
    current_year = datetime_to_lectureyear(timezone.now())

    choices = []
    for year in range(1990, current_year + 2):
        choices.append((year, "{}-{}".format(year, year + 1)))
    choices.reverse()

    return choices


class ThabloidAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initial["year"] = datetime_to_lectureyear(timezone.now())
        self.fields["year"] = forms.ChoiceField(
            label="Academic year", choices=association_year_choices()
        )


@admin.register(Thabloid)
class ThabloidAdmin(admin.ModelAdmin):
    form = ThabloidAdminForm
    list_filter = ("year",)
