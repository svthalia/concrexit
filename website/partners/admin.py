from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from partners.models import (
    Partner,
    PartnerImage,
    Vacancy,
    VacancyCategory,
)


class PartnerImageInline(admin.StackedInline):
    """Class to show partner images inline in the admin."""

    model = PartnerImage


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Class to show partners in the admin."""

    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "is_active", "is_main_partner", "is_local_partner")
    search_fields = ("name", "city")
    list_filter = ("is_active",)
    inlines = (PartnerImageInline,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "link",
                    "company_profile",
                    "logo",
                    "site_header",
                    "is_active",
                    "is_main_partner",
                    "is_local_partner",
                )
            },
        ),
        (
            _("Address"),
            {"fields": ("address", "address2", "zip_code", "city", "country")},
        ),
    )


@admin.register(VacancyCategory)
class VacancyCategoryAdmin(admin.ModelAdmin):
    """Class to show vacancy categories in the admin."""

    prepopulated_fields = {"slug": ("name",)}
    fields = ["name", "slug"]


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    """Class to show vacancies in the admin."""

    list_display = ("title", "partner", "company_name")

    list_select_related = ("partner",)
    search_fields = (
        "title",
        "partner__name",
        "company_name",
    )
    fieldsets = (
        (None, {"fields": ("title", "description", "link", "location", "keywords")}),
        (_("Existing partner"), {"fields": ("partner",)}),
        (
            _("Other partner"),
            {
                "fields": (
                    "company_name",
                    "company_logo",
                )
            },
        ),
        (_("Categories"), {"fields": ("categories",)}),
    )
