import os

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from photos.models import Album, Photo
from photos.services import (
    check_shared_album_token,
    get_annotated_accessible_albums,
    is_album_accessible,
)
from thaliawebsite.views import PagedView
from utils.media.services import get_media_url

COVER_FILENAME = "cover.jpg"


@method_decorator(login_required, "dispatch")
class IndexView(PagedView):
    model = Album
    paginate_by = 16
    template_name = "photos/index.html"
    context_object_name = "albums"
    keywords = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.keywords = request.GET.get("keywords", "").split()

    def get_queryset(self):
        albums = Album.objects.filter(hidden=False).select_related("_cover")
        for key in self.keywords:
            albums = albums.filter(**{"title__icontains": key})
        albums = get_annotated_accessible_albums(self.request, albums)
        albums = albums.order_by("-date")
        return albums

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["keywords"] = self.keywords
        return context


class _BaseAlbumView(TemplateView):
    template_name = "photos/album.html"

    def get_album(self, **kwargs):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        album = self.get_album(**kwargs)

        context["album"] = album
        photos = album.photo_set.filter(hidden=False).select_properties("num_likes")

        # Fix select_properties dropping the default ordering.
        photos = photos.order_by("pk")

        context["photos"] = photos
        return context


@method_decorator(login_required, "dispatch")
class AlbumDetailView(_BaseAlbumView):
    """Render an album, if it is accessible by the user."""

    def get_album(self, **kwargs):
        slug = kwargs.get("slug")
        album = get_object_or_404(Album, slug=slug)

        if not is_album_accessible(self.request, album):
            raise Http404("Sorry, you're not allowed to view this album")

        return album


class SharedAlbumView(_BaseAlbumView):
    """Render a shared album if the correct token is provided."""

    def get_album(self, **kwargs):
        slug = kwargs.get("slug")
        token = kwargs.get("token")
        album = get_object_or_404(Album, slug=slug)

        check_shared_album_token(album, token)

        return album


def _photo_path(obj, filename):
    """Return the path to a Photo."""
    photoname = os.path.basename(filename)
    albumpath = os.path.join(obj.photosdir, obj.dirname)
    photopath = os.path.join(albumpath, photoname)
    get_object_or_404(Photo.objects.filter(album=obj, file=photopath))
    return photopath


def _download(request, obj, filename):
    """Download a photo.

    This function provides a layer of indirection for shared albums.
    """
    photopath = _photo_path(obj, filename)
    photo = get_object_or_404(Photo.objects.filter(album=obj, file=photopath))
    return redirect(get_media_url(photo.file, f"{obj.slug}-{filename}"))


@login_required
def download(request, slug, filename):
    """Download a photo if the album of the photo is accessible by the user."""
    obj = get_object_or_404(Album, slug=slug)
    if is_album_accessible(request, obj):
        return _download(request, obj, filename)
    raise Http404("Sorry, you're not allowed to view this album")


def shared_download(request, slug, token, filename):
    """Download a photo from a shared album if the album token is provided."""
    obj = get_object_or_404(Album, slug=slug)
    check_shared_album_token(obj, token)
    return _download(request, obj, filename)


@method_decorator(login_required, "dispatch")
class LikedPhotoView(PagedView):
    model = Photo
    paginate_by = 16
    template_name = "photos/liked-photos.html"
    context_object_name = "photos"

    def get_queryset(self):
        return (
            Photo.objects.filter(likes__member=self.request.member, album__hidden=False)
            .select_related("album")
            .select_properties("num_likes")
            .order_by("-album__date")
        )
