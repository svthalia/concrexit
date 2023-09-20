from django.contrib import admin, messages
from django.db.models import Count
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

from django_filepond_widget.fields import FilePondFile

from .forms import AlbumForm
from .models import Album, Like, Photo
from .services import extract_archive, save_photo

album_uploaded = Signal()


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
    prepopulated_fields = {
        "slug": (
            "date",
            "title",
        )
    }
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
            try:
                extract_archive(request, obj, archive)
                album_uploaded.send(sender=None, album=obj)
            except Exception as e:
                raise e
            finally:
                if isinstance(archive, FilePondFile):
                    archive.remove()

            messages.add_message(
                request,
                messages.WARNING,
                _("Full-sized photos will not be saved on the Thalia-website."),
            )
            messages.add_message(
                request,
                messages.WARNING,
                "Thumbnails have not yet been generated. The first time you visit the "
                "album (both in the website and the app) will be slow. Please do so now.",
            )

    def get_deleted_objects(self, objs, request):
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = super().get_deleted_objects(objs, request)

        # Drop any missing delete permissions. If the user has `delete_album` permission,
        # they should automatically be allowed to cascade e.g. related pushnotifications.
        return deleted_objects, model_count, set(), protected


class LikeInline(admin.StackedInline):
    model = Like
    extra = 0


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Model for Photo admin page."""

    list_display = (
        "__str__",
        "album",
        "num_likes",
    )
    search_fields = ("file",)
    list_filter = ("album",)
    exclude = ("_digest",)

    inlines = [
        LikeInline,
    ]

    def get_deleted_objects(self, objs, request):
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = super().get_deleted_objects(objs, request)

        return deleted_objects, model_count, set(), protected

    def save_model(self, request, obj, form, change):
        """Save new Photo."""
        super().save_model(request, obj, form, change)
        if change and obj.original_file == obj.file.name:
            return

        if save_photo(obj, obj.file, obj.file.name):
            messages.add_message(
                request,
                messages.WARNING,
                _("Full-sized photos will not be saved on the Thalia-website."),
            )
        else:
            messages.add_message(
                request, messages.ERROR, _("This photo already exists in the album.")
            )
