from django.contrib import admin

from partners.models import (Partner, PartnerEvent, PartnerImage,
                             Vacancy, VacancyCategory)
from utils.translation import TranslatedModelAdmin


class PartnerImageInline(admin.StackedInline):
    """Class to show partner images inline in the admin."""

    model = PartnerImage


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Class to show partners in the admin."""

    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'is_active', 'is_main_partner',
                    'is_local_partner')
    search_fields = ('name', 'city')
    list_filter = ('is_active',)
    inlines = (PartnerImageInline,)

    fieldsets = (
        (None, {
            'fields': (
                'name', 'slug', 'link',
                'company_profile', 'logo', 'site_header',
                'is_active', 'is_main_partner', 'is_local_partner',
            )
        }),
        ('Address', {
            'fields': ('address', 'zip_code', 'city')

        }),
    )


@admin.register(VacancyCategory)
class VacancyCategoryAdmin(TranslatedModelAdmin):
    """Class to show vacancy categories in the admin."""

    prepopulated_fields = {"slug": ("name_en",)}
    fields = ['name', 'slug']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    """Class to show vacancies in the admin."""

    list_display = ('title', 'partner', 'company_name', 'expiration_date')
    search_fields = ('title', 'partner__name', 'company_name',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'link',)
        }),
        ('Existing Partner', {
            'fields': ('partner',)
        }),
        ('Other Partner', {
            'fields': ('company_name', 'company_logo',)
        }),
        ('Categories', {
            'fields': ('categories',)
        }),
        ('Other', {
            'fields': ('remarks', 'expiration_date')
        })
    )


@admin.register(PartnerEvent)
class PartnerEventAdmin(TranslatedModelAdmin):
    """Class to show partner events in the admin."""

    fields = ('partner', 'other_partner', 'title', 'description', 'location',
              'start', 'end', 'url', 'published')
    list_display = ('title', 'start', 'end',
                    'partner', 'published')
    list_filter = ('start', 'published')
    search_fields = ('title', 'partner__name')
