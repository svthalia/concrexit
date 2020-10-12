import os
from tempfile import gettempdir
from zipfile import ZipFile

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language
from django_sendfile import sendfile

from photos.models import Album, Photo
from photos.services import (
    check_shared_album_token,
    get_annotated_accessible_albums,
    is_album_accessible,
)

COVER_FILENAME = "cover.jpg"


@login_required
def index(request):
    """Render the index page showing multiple album cards."""
    keywords = request.GET.get("keywords", "").split()

    # Only show published albums
    albums = Album.objects.filter(hidden=False)
    for key in keywords:
        albums = albums.filter(**{f"title_{get_language()}__icontains": key})

    albums = get_annotated_accessible_albums(request, albums)

    albums = albums.order_by("-date")
    paginator = Paginator(albums, 16)

    page = request.GET.get("page")
    page = 1 if page is None or not page.isdigit() else int(page)
    try:
        albums = paginator.page(page)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        albums = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    # Show the two pages before and after the current page
    page_range_start = max(1, page - 2)
    page_range_stop = min(page + 3, paginator.num_pages + 1)

    # Add extra pages if we show less than 5 pages
    page_range_start = min(page_range_start, page_range_stop - 5)
    page_range_start = max(1, page_range_start)

    # Add extra pages if we still show less than 5 pages
    page_range_stop = max(page_range_stop, page_range_start + 5)
    page_range_stop = min(page_range_stop, paginator.num_pages + 1)

    page_range = range(page_range_start, page_range_stop)

    return render(
        request,
        "photos/index.html",
        {"albums": albums, "page_range": page_range, "keywords": keywords},
    )


def _render_album_page(request, album):
    """Render album.html for a specified album."""
    context = {"album": album, "photos": album.photo_set.filter(hidden=False)}
    return render(request, "photos/album.html", context)


@login_required
def detail(request, slug):
    """Render an album, if it accessible by the user."""
    obj = get_object_or_404(Album, slug=slug)
    if is_album_accessible(request, obj):
        return _render_album_page(request, obj)
    raise Http404("Sorry, you're not allowed to view this album")


def shared_album(request, slug, token):
    """Render a shared album if the correct token is provided."""
    obj = get_object_or_404(Album, slug=slug)
    check_shared_album_token(obj, token)
    return _render_album_page(request, obj)


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
    return sendfile(request, photo.file.path, attachment=True)


def _album_download(request, obj):
    """Download an album.

    This function provides a layer of indirection for shared albums.
    """
    albumpath = os.path.join(obj.photospath, obj.dirname)
    zipfilename = os.path.join(gettempdir(), "{}.zip".format(obj.dirname))
    if not os.path.exists(zipfilename):
        with ZipFile(zipfilename, "w") as f:
            pictures = [os.path.join(albumpath, x) for x in os.listdir(albumpath)]
            for picture in pictures:
                f.write(picture, arcname=os.path.basename(picture))
    return sendfile(request, zipfilename, attachment=True)


@login_required
def download(request, slug, filename):
    """Download a photo if the album of the photo is accessible by the user."""
    obj = get_object_or_404(Album, slug=slug)
    if is_album_accessible(request, obj):
        return _download(request, obj, filename)
    raise Http404("Sorry, you're not allowed to view this album")


@login_required
def album_download(request, slug):
    """Download an album if the album is accessible by the user."""
    obj = get_object_or_404(Album, slug=slug)
    if is_album_accessible(request, obj):
        return _album_download(request, obj)
    raise Http404("Sorry, you're not allowed to view this album")


def shared_download(request, slug, token, filename):
    """Download a photo from a shared album if the album token is provided."""
    obj = get_object_or_404(Album, slug=slug)
    check_shared_album_token(obj, token)
    return _download(request, obj, filename)


def shared_album_download(request, slug, token):
    """Download a shared album if the album token is provided."""
    obj = get_object_or_404(Album, slug=slug)
    check_shared_album_token(obj, token)
    return _album_download(request, obj)
