from django.contrib import admin

from partners.models import (Partner, PartnerEvent, PartnerImage,
                             Vacancy, VacancyCategory)
from utils.translation import TranslatedModelAdmin


class PartnerImageInline(admin.StackedInline):
    model = PartnerImage


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'is_active', 'is_main_partner',)
    inlines = (PartnerImageInline,)

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


@admin.register(VacancyCategory)
class VacancyCategoryAdmin(TranslatedModelAdmin):
    prepopulated_fields = {"slug": ("name_en",)}
    fields = ['name', 'slug']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'company_name', 'expiration_date')

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
    fields = ['partner', 'title', 'description', 'location', 'start', 'end',
              'url', 'published']
    list_display = ('title', 'start', 'end',
                    'partner', 'published')
    list_filter = ('start', 'published')
