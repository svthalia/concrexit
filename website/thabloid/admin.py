from django.contrib import admin

from .models import Thabloid


class ThabloidAdmin(admin.ModelAdmin):
    list_filter = ('year', )


admin.site.register(Thabloid, ThabloidAdmin)
