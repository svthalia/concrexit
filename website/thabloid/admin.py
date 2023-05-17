from django import forms
from django.contrib import admin
from django.utils import timezone

from thabloid.models.thabloid import Thabloid
from thabloid.models.thabloid_user import ThabloidUser
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


@admin.register(ThabloidUser)
class ThabloidUserAdmin(admin.ModelAdmin):
    list_display = ("__str__", "get_wants_thabloid")

    fields = ("get_wants_thabloid",)

    readonly_fields = ("get_wants_thabloid",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_properties("wants_thabloid")
        return queryset

    def get_wants_thabloid(self, obj):
        return obj.wants_thabloid

    get_wants_thabloid.boolean = True

    get_wants_thabloid.short_description = "Wants Thabliod"
