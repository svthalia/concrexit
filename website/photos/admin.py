from django.contrib import admin
from django import forms
from django.conf import settings
from django.core.files.base import ContentFile

from .models import Album, Photo

import os
from zipfile import ZipFile


class AlbumForm(forms.ModelForm):
    album_archive = forms.FileField(
        required=False,
        help_text="Uploading a zip file adds all contained images as photos.",
    )

    class Meta:
        exclude = ['dirname']


class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('date', 'title',)}
    form = AlbumForm

    def save_model(self, request, obj, form, change):
        obj.save()
        archive = form.cleaned_data.get('album_archive', None)
        if archive is None:
            return
        with ZipFile(archive) as zip_file:
            path = os.path.join(settings.MEDIA_ROOT, 'photos', obj.dirname)
            os.makedirs(path, exist_ok=True)
            # Notably, this can also be used to add photos to existing albums
            for photo in zip_file.namelist():
                # TODO this may still need to be a bit more robust
                # e.g. duplicate names cause overwriting (but are unlikely)
                # Flatten any subdirectories
                photo_filename = os.path.basename(photo)
                # Skip directories (which do not have a basename)
                if not photo_filename:
                    continue
                # Cannot use .extract as that would recreate directory paths
                photo_obj = Photo()
                photo_obj.album = obj
                with zip_file.open(photo) as f:
                    photo_obj.file.save(photo_filename, ContentFile(f.read()))
                photo_obj.save()

admin.site.register(Album, AlbumAdmin)
admin.site.register(Photo)
