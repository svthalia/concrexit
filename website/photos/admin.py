from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

from django_filepond_widget.fields import FilePondFile

from .forms import AlbumForm
from .models import Album, Like, Photo
from .services import extract_archive

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
                with transaction.atomic():
                    # We make the upload atomic separately, so we can keep using the db if it fails.
                    # See https://docs.djangoproject.com/en/4.2/topics/db/transactions/#handling-exceptions-within-postgresql-transactions.
                    extract_archive(request, obj, archive)
                album_uploaded.send(sender=None, album=obj)
            except Exception:
                raise
            finally:
                if isinstance(archive, FilePondFile):
                    archive.remove()

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
