import os
from datetime import date

from django.db.models import QuerySet
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from facedetection.models import ReferenceFace
from photos.models import Album, Photo
from photos.services import (
    check_shared_album_token,
    get_annotated_accessible_albums,
    is_album_accessible,
)
from thaliawebsite.views import PagedView
from utils.media.services import fetch_thumbnails, get_media_url
from utils.snippets import datetime_to_lectureyear
from django.db.models import Q

COVER_FILENAME = "cover.jpg"


class IndexView(LoginRequiredMixin, PagedView):
    model = Album
    paginate_by = 16
    template_name = "photos/index.html"
    context_object_name = "albums"
    keywords = None
    query_filter = ""
    year_range = []

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        current_lectureyear = datetime_to_lectureyear(date.today())
        self.year_range = list(
            reversed(range(current_lectureyear - 5, current_lectureyear + 1))
        )
        self.keywords = request.GET.get("keywords", "").split() or None
        self.query_filter = kwargs.get("year", None)

    def get_queryset(self) -> QuerySet:
        albums = Album.objects.filter(hidden=False, is_processing=False).select_related(
            "_cover"
        )
        # We split on greater than the 7th month of the year (July),
        # to make sure the introduction week photos (from August) are the first on each year page.
        if self.query_filter == "older":
            albums = albums.filter(
                Q(date__year=self.year_range[-1], date__month__gt=7)
                | Q(date__year__lt=self.year_range[-1])
            )
        elif self.query_filter:
            albums = albums.filter(
                Q(date__year=self.query_filter, date__month__gt=7)
                | Q(date__year=int(self.query_filter) + 1, date__month__lt=8)
            )
        if self.keywords:
            for key in self.keywords:
                albums = albums.filter(title__icontains=key)
        albums = get_annotated_accessible_albums(self.request, albums)
        albums = albums.order_by("-date")
        return albums

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "filter": self.query_filter,
                "year_range": self.year_range,
                "keywords": self.keywords,
            }
        )
        fetch_thumbnails([x.cover.file for x in context["object_list"] if x.cover])

        context["has_rejected_reference_faces"] = (
            self.request.member.reference_faces.filter(
                status=ReferenceFace.Status.REJECTED,
                marked_for_deletion_at__isnull=True,
            ).exists()
        )

        context["has_reference_faces"] = self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).exists()
        return context


class _BaseAlbumView(TemplateView):
    template_name = "photos/album.html"

    def get_album(self, **kwargs):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        album = self.get_album(**kwargs)

        context["album"] = album
        photos = album.photo_set.select_properties("num_likes")

        # Fix select_properties dropping the default ordering.
        photos = photos.order_by("pk")

        # Prefetch thumbnails for efficiency
        fetch_thumbnails([p.file for p in photos])

        context["photos"] = photos
        return context


class AlbumDetailView(LoginRequiredMixin, _BaseAlbumView):
    """Render an album, if it is accessible by the user."""

    def get_album(self, **kwargs):
        slug = kwargs.get("slug")
        album = get_object_or_404(
            Album.objects.filter(hidden=False, is_processing=False), slug=slug
        )

        if not is_album_accessible(self.request, album):
            raise Http404("Sorry, you're not allowed to view this album")

        return album


class SharedAlbumView(_BaseAlbumView):
    """Render a shared album if the correct token is provided."""

    def get_album(self, **kwargs):
        slug = kwargs.get("slug")
        token = kwargs.get("token")
        album = get_object_or_404(
            Album.objects.filter(hidden=False, is_processing=False), slug=slug
        )

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
    return redirect(get_media_url(photo.file, attachment=f"{obj.slug}-{filename}"))


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


class LikedPhotoView(LoginRequiredMixin, PagedView):
    model = Photo
    paginate_by = 16
    template_name = "photos/liked-photos.html"
    context_object_name = "photos"

    def get_queryset(self):
        photos = (
            Photo.objects.filter(
                likes__member=self.request.member,
                album__hidden=False,
                album__is_processing=False,
            )
            .select_related("album")
            .select_properties("num_likes")
            .order_by("-album__date")
        )
        return photos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fetch_thumbnails([p.file for p in context["photos"]])

        return context


class MostLikedPhotoView(LoginRequiredMixin, PagedView):
    model = Photo
    paginate_by = 16
    template_name = "photos/mostliked-photos.html"
    context_object_name = "photos"

    def get_queryset(self):
        photos = (
            Photo.objects.filter(
                album__hidden=False,
                album__is_processing=False,
            )
            .select_related("album")
            .select_properties("num_likes")
            .filter(num_likes__gt=0)
            .order_by("-num_likes")
        )
        return photos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fetch_thumbnails([p.file for p in context["photos"]])

        return context
