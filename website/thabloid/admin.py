import csv

from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from queryable_properties.admin import QueryablePropertiesAdmin

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
class ThabloidUserAdmin(QueryablePropertiesAdmin):
    """Admin that shows only current members that want to receive the Thabloid."""

    list_display = ("first_name", "last_name", "address")

    fields = (
        "first_name",
        "last_name",
        "street",
        "street2",
        "postal_code",
        "city",
        "country",
    )
    readonly_fields = fields

    actions = ["address_csv_export"]

    def get_queryset(self, request):
        qs = ThabloidUser.current_members.filter(blacklistedthabloiduser__isnull=True)

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    @admin.display(description="Address")
    def street(self, obj):
        return obj.profile.address_street

    @admin.display(description="Address line 2")
    def street2(self, obj):
        return obj.profile.address_street

    @admin.display(description="Postal code")
    def postal_code(self, obj):
        return obj.profile.address_postal_code

    @admin.display(description="City")
    def city(self, obj):
        return obj.profile.address_city

    @admin.display(description="Country")
    def country(self, obj):
        return obj.profile.get_address_country_display()

    @admin.display(description="Address (short)")
    def address(self, obj):
        return f"{obj.profile.address_street}, {obj.profile.address_postal_code}, {obj.profile.address_city}"

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def address_csv_export(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="thabloid_addresses.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "First name",
                "Last name",
                "Address",
                "Address line 2",
                "Postal code",
                "City",
                "Country",
            ]
        )
        for user in queryset.exclude(profile=None):
            writer.writerow(
                [
                    user.first_name,
                    user.last_name,
                    user.profile.address_street,
                    user.profile.address_street2,
                    user.profile.address_postal_code,
                    user.profile.address_city,
                    user.profile.get_address_country_display(),
                ]
            )
        return response

    address_csv_export.short_description = "Download addresses for selected users"
