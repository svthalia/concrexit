from django.contrib import admin
from django.contrib import messages
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .forms import AlbumForm
from .models import Album, Photo
from .services import extract_archive, save_photo


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """Model for Album admin page."""

    list_display = ("title", "date", "num_photos", "hidden", "shareable")
    fields = (
        "title",
        "slug",
        "date",
        "event",
        "hidden",
        "shareable",
        "album_archive",
        "_cover",
    )
    search_fields = ("title", "date")
    list_filter = ("hidden", "shareable")
    date_hierarchy = "date"
    prepopulated_fields = {"slug": ("date", "title",)}
    form = AlbumForm

    def get_queryset(self, request):
        """Get Albums and add the amount of photos as an annotation."""
        return Album.objects.annotate(photos_count=Count("photo"))

    def num_photos(self, obj):
        """Pretty-print the number of photos."""
        return obj.photos_count

    num_photos.short_description = _("Number of photos")
    num_photos.admin_order_field = "photos_count"

    def save_model(self, request, obj, form, change):
        """Save the new Album by extracting the archive."""
        super().save_model(request, obj, form, change)

        archive = form.cleaned_data.get("album_archive", None)
        if archive is not None:
            extract_archive(request, obj, archive)

            messages.add_message(
                request,
                messages.WARNING,
                _("Full-sized photos will not be saved on the Thalia-website."),
            )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Model for Photo admin page."""

    list_display = ("__str__", "album", "hidden")
    search_fields = ("file",)
    list_filter = ("album", "hidden")
    exclude = ("_digest",)

    def save_model(self, request, obj, form, change):
        """Save new Photo."""
        super().save_model(request, obj, form, change)
        if change and obj.original_file == obj.file.path:
            return

        if save_photo(obj):
            messages.add_message(
                request,
                messages.WARNING,
                _("Full-sized photos will not be saved on the Thalia-website."),
            )
        else:
            messages.add_message(
                request, messages.ERROR, _("This photo already exists in the album.")
            )
