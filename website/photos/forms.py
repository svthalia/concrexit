from django import forms
from django.utils.translation import gettext_lazy as _

from django_filepond_widget.fields import FilePondField

from photos.models import Album, Photo
from photos.validators import ArchiveFileTypeValidator


class AlbumForm(forms.ModelForm):
    """Class for an album submission form."""

    def __init__(self, *args, **kwargs):
        """Initialize AlbumForm.

        Set the cover options to photos from the specified album.
        https://stackoverflow.com/questions/4391776/django-admin-inline-forms-limit-foreign-key-queryset-to-a-set-of-values#4392047
        """
        super().__init__(*args, **kwargs)
        if "instance" in kwargs and "_cover" in self.fields:
            self.fields["_cover"].queryset = Photo.objects.filter(album=self.instance)

    album_archive = FilePondField(
        required=False,
        help_text=_("Uploading a zip or tar file adds all contained images as photos."),
        validators=[ArchiveFileTypeValidator()],
    )

    class Meta:
        """Meta class for AlbumForm."""

        model = Album
        fields = (
            "title",
            "date",
            "slug",
            "hidden",
            "new_album_notification",
            "shareable",
            "_cover",
        )
