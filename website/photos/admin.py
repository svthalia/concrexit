from django.contrib import admin
from django import forms

from .models import Album


class AlbumForm(forms.ModelForm):
    album_archive = forms.FileField()

    class Meta:
        exclude = ['dirname']

class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('date', 'title',)}
    form = AlbumForm

admin.site.register(Album, AlbumAdmin)
