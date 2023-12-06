from django.contrib import admin, messages
from django.db.models import Count
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

from .forms import AlbumForm
from .models import Album, Like, Photo
from .tasks import process_album_upload

album_uploaded = Signal()  # remove?


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """Model for Album admin page."""

    list_display = (
        "title",
        "date",
        "num_photos",
        "hidden",
        "is_processing",
        "shareable",
    )
    fields = (
        "title",
        "slug",
        "date",
        "event",
        "hidden",
        "is_processing",
        "shareable",
        "album_archive",
        "_cover",
    )
    readonly_fields = ("is_processing",)
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

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj is None:
            fields.remove("_cover")

        return fields

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

        archive = form.cleaned_data.get("album_archive")
        if archive is not None:
            obj.is_processing = True
            obj.save()
            process_album_upload.delay(
                archive.temporary_upload.upload_id, obj.id
            )  # look for album_id

        self.message_user(
            request,
            "Album is being processed, you will be notified when it is ready.",
            messages.INFO,
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
