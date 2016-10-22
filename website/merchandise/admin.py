from django.contrib import admin

from utils.translation import TranslatedModelAdmin

from .models import MerchandiseItem


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(TranslatedModelAdmin):
    fields = ('name', 'price',
              'description', 'image',)
