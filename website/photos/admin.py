from django.contrib import admin
from django.contrib import messages
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from utils.translation import TranslatedModelAdmin
from .forms import AlbumForm
from .models import Album, Photo
from .services import extract_archive, save_photo


class AlbumAdmin(TranslatedModelAdmin):
    list_display = ("title", "date", "num_photos", "hidden", "shareable")
    fields = ("title", "slug", "date", "hidden", "shareable", "album_archive", "_cover")
    search_fields = ("title", "date")
    list_filter = ("hidden", "shareable")
    date_hierarchy = "date"
    prepopulated_fields = {"slug": ("date", "title_en",)}
    form = AlbumForm

    def get_queryset(self, request):
        return Album.objects.annotate(photos_count=Count("photo"))

    def num_photos(self, obj):
        """Pretty-print the number of photos"""
        return obj.photos_count

    num_photos.short_description = _("Number of photos")
    num_photos.admin_order_field = "photos_count"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        archive = form.cleaned_data.get("album_archive", None)
        if archive is not None:
            extract_archive(request, obj, archive)

            messages.add_message(
                request,
                messages.WARNING,
                _("Full-sized photos will not be saved on the Thalia-website."),
            )


class PhotoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "album", "hidden")
    search_fields = ("file",)
    list_filter = ("album", "hidden")
    exclude = ("_digest",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
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


admin.site.register(Album, AlbumAdmin)
admin.site.register(Photo, PhotoAdmin)
