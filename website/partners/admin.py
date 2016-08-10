from django.contrib import admin

from utils.translation import TranslatedModelAdmin

from partners.models import (
    Partner,
    PartnerImage,
    VacancyCategory,
)


class PartnerImageInline(admin.StackedInline):
    model = PartnerImage


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {
            'fields': (
                'is_active', 'is_main_partner', 'name', 'slug', 'link',
                'company_profile', 'logo', 'site_header'
            )
        }),
        ('Address', {
            'fields': ('address', 'zip_code', 'city')

        }),
    )

    inlines = (PartnerImageInline,)


@admin.register(VacancyCategory)
class VacancyCategoryAdmin(TranslatedModelAdmin):
    prepopulated_fields = {"slug": ("name_en",)}
    fields = ['name', 'slug']
