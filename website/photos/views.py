import os
from tempfile import gettempdir
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousFileOperation
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from sendfile import sendfile

from photos import services
from utils.views import _private_thumbnails_unauthed
from .models import Album

COVER_FILENAME = 'cover.jpg'


@login_required
def index(request):
    # Only show published albums
    albums = Album.objects.filter(hidden=False)

    albums = services.get_annotated_accessible_albums(request, albums)

    albums = albums.order_by('-date')
    paginator = Paginator(albums, 12)

    page = request.GET.get('page')
    page = 1 if page is None or not page.isdigit() else int(page)
    try:
        albums = paginator.page(page)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        albums = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    page_range = range(1, paginator.num_pages + 1)
    if paginator.num_pages > 7:
        if page > 3:
            page_range_end = paginator.num_pages
            if page + 3 <= paginator.num_pages:
                page_range_end = page + 3

            page_range = range(page - 2, page_range_end)
            while page_range.stop - page_range.start < 5:
                page_range = range(page_range.start - 1, page_range.stop)
        else:
            page_range = range(1, 6)

    return render(request, 'photos/index.html', {'albums': albums,
                                                 'page_range': page_range})


def _render_album_page(request, album):
    context = {
        'album': album,
        'photos': album.photo_set.filter(hidden=False)
    }
    return render(request, 'photos/album.html', context)


@login_required
def album(request, slug):
    album = get_object_or_404(Album, slug=slug)
    if services.is_album_accessible(request, album):
        return _render_album_page(request, album)
    raise Http404("Sorry, you're not allowed to view this album")


def _checked_shared_album(slug, token):
    album = get_object_or_404(Album, slug=slug)
    if token != album.access_token:
        raise Http404("Invalid token.")
    return album


def shared_album(request, slug, token):
    album = _checked_shared_album(slug, token)
    return _render_album_page(request, album)


def _download(request, original_path):
    """This function provides a layer of indirection for shared albums

    Checks for some path traversal:

    >>> from django.test import RequestFactory
    >>> r = RequestFactory().get('/photos/download/../../../../../etc/passwd')
    >>> _download(r, '../../../../../../../etc/passwd')  #doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    django.core.exceptions.SuspiciousFileOperation: ...
    """
    photopath = os.path.join(settings.MEDIA_ROOT, 'photos')

    path = os.path.normpath(
        os.path.join(photopath, *original_path.split('/')[1:]))

    if not os.path.commonpath([photopath, path]) == photopath:
        raise SuspiciousFileOperation(
            "Path traversal detected: someone tried to download "
            "{}, input: {}".format(path, original_path))
    if not os.path.isfile(path):
        raise Http404("Photo not found.")
    return sendfile(request, path, attachment=True)


def _album_download(request, slug):
    """This function provides a layer of indirection for shared albums"""
    album = get_object_or_404(Album, slug=slug)
    albumpath = os.path.join(album.photospath, album.dirname)
    pictures = [os.path.join(albumpath, x) for x in os.listdir(albumpath)]
    zipfilename = os.path.join(gettempdir(),
                               '{}.zip'.format(album.dirname))
    if not os.path.exists(zipfilename):
        with ZipFile(zipfilename, 'w') as f:
            for picture in pictures:
                f.write(picture, arcname=os.path.basename(picture))
    return sendfile(request, zipfilename, attachment=True)


@login_required
def download(request, path):
    return _download(request, path)


@login_required
def album_download(request, slug):
    return _album_download(request, slug)


def shared_download(request, slug, token, path):
    _checked_shared_album(slug, token)
    return _download(request, path)


def shared_thumbnail(request, slug, token, size_fit, path):
    _checked_shared_album(slug, token)
    return _private_thumbnails_unauthed(request, size_fit, path)
