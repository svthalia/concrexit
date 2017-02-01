import os
import tarfile
from zipfile import ZipFile, is_zipfile, ZipInfo

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.files.base import ContentFile

from .models import Album, Photo


class AlbumForm(forms.ModelForm):

    # Excuse my french
    # https://stackoverflow.com/questions/4391776/django-admin-inline-forms-limit-foreign-key-queryset-to-a-set-of-values#4392047
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.fields['_cover'].queryset = Photo.objects.filter(
                album=self.instance)

    album_archive = forms.FileField(
        required=False,
        help_text="Uploading a zip or tar file adds all contained images as "
                  "photos.",
    )

    class Meta:
        exclude = ['dirname']


def save_photo(request, archive_file, photo, album):
    # zipfile and tarfile are inconsistent
    if isinstance(photo, ZipInfo):
        photo_filename = photo.filename
        extract_file = archive_file.open
    elif isinstance(photo, tarfile.TarInfo):
        photo_filename = photo.name
        extract_file = archive_file.extractfile
    else:
        return

    # Ignore directories
    if not os.path.basename(photo_filename):
        return

    photo_obj = Photo()
    photo_obj.album = album
    try:
        with extract_file(photo) as f:
            photo_obj.file.save(photo_filename, ContentFile(f.read()))
    except (OSError, AttributeError):
        messages.add_message(request, messages.WARNING,
                             "Ignoring {}".format(photo_filename))
    else:
        photo_obj.save()


class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('date', 'title',)}
    form = AlbumForm

    def save_model(self, request, obj, form, change):
        obj.save()

        archive = form.cleaned_data.get('album_archive', None)
        if archive is None:
            return

        iszipfile = is_zipfile(archive)
        archive.seek(0)

        if iszipfile:
            with ZipFile(archive) as zip_file:
                for photo in zip_file.infolist():
                    save_photo(request, zip_file, photo, obj)
        else:
            # is_tarfile only supports filenames, so we cannot use that
            try:
                with tarfile.open(fileobj=archive) as tar_file:
                    for photo in tar_file.getmembers():
                        save_photo(request, tar_file, photo, obj)
            except tarfile.ReadError:
                return

        messages.add_message(request, messages.WARNING,
                             "Full-sized photos will not be saved on the "
                             "Thalia-website.")


class PhotoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        messages.add_message(request, messages.WARNING,
                             "Full-sized photos will not be saved on the "
                             "Thalia-website.")

admin.site.register(Album, AlbumAdmin)
admin.site.register(Photo, PhotoAdmin)
