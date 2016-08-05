from django.contrib import admin

from partners.models import Partner, PartnerImage


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
