from django.contrib import admin
from django import forms
from django.conf import settings

from .models import Album

import os
import shutil
from zipfile import ZipFile


class AlbumForm(forms.ModelForm):
    album_archive = forms.FileField()

    class Meta:
        exclude = ['dirname']


class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('date', 'title',)}
    form = AlbumForm

    def save_model(self, request, obj, form, change):
        obj.save()
        archive = form.cleaned_data.get('album_archive', None)
        path = os.path.join(settings.MEDIA_ROOT, 'photos', obj.dirname)
        with ZipFile(archive) as zip_file:
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
                source = zip_file.open(photo)
                target = open(os.path.join(path, photo_filename), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)

admin.site.register(Album, AlbumAdmin)
