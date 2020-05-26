from django import forms

from photos.models import Photo
from photos.validators import ArchiveFileTypeValidator
from django.utils.translation import gettext_lazy as _


class AlbumForm(forms.ModelForm):

    # Excuse my french
    # https://stackoverflow.com/questions/4391776/django-admin-inline-forms-limit-foreign-key-queryset-to-a-set-of-values#4392047
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs and "_cover" in self.fields:
            self.fields["_cover"].queryset = Photo.objects.filter(album=self.instance)

    album_archive = forms.FileField(
        required=False,
        help_text=_("Uploading a zip or tar file adds all contained images as photos."),
        validators=[ArchiveFileTypeValidator()],
    )

    class Meta:
        exclude = ["dirname"]
