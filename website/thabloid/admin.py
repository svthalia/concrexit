from django import forms
from django.contrib import admin
from django.utils import timezone

from thabloid.models import Thabloid
from utils.snippets import datetime_to_lectureyear


def association_year_choices():
    """Return the academic years Thalia existed."""
    current_year = datetime_to_lectureyear(timezone.now())

    choices = []
    for year in range(1990, current_year + 2):
        choices.append((year, f"{year}-{year + 1}"))
    choices.reverse()

    return choices


class ThabloidAdminForm(forms.ModelForm):
    """Admin form for Thabloid objects."""

    def __init__(self, *args, **kwargs):
        """Initialize form and set the year choices."""
        super().__init__(*args, **kwargs)

        self.initial["year"] = datetime_to_lectureyear(timezone.now())
        self.fields["year"] = forms.ChoiceField(
            label="Academic year", choices=association_year_choices()
        )


@admin.register(Thabloid)
class ThabloidAdmin(admin.ModelAdmin):
    """Admin class for Thabloid objects."""

    form = ThabloidAdminForm
    list_filter = ("year",)
