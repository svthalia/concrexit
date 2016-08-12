from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Album
from utils.snippets import sanitize_path
from utils.views import _private_thumbnails_unauthed

from sendfile import sendfile
import os

COVER_FILENAME = 'cover.jpg'


@login_required
def index(request):
    albums = Album.objects.filter(hidden=False).order_by('-date')

    paginator = Paginator(albums, 12)
    page = request.GET.get('page')
    try:
        albums = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        albums = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        albums = paginator.page(paginator.num_pages)
    return render(request, 'photos/index.html', {'albums': albums})


@login_required
def album(request, slug):
    album = get_object_or_404(Album, slug=slug)
    context = {'album': album, 'photos': album.photo_set.filter(hidden=False)}
    return render(request, 'photos/album.html', context)


def _checked_shared_album(slug, token):
    album = get_object_or_404(Album, slug=slug)
    if token != album.access_token:
        raise Http404("Invalid token.")
    return album


def shared_album(request, slug, token):
    album = _checked_shared_album(slug, token)
    return render(request, 'photos/album.html', {'album': album})


def _download(request, path):
    """This function provides a layer of indirection for shared albums"""
    path = sanitize_path(path)
    path = os.path.join(settings.MEDIA_ROOT, 'photos', *path.split('/')[1:])
    if not os.path.isfile(path):
        raise Http404("Photo not found.")
    return sendfile(request, path, attachment=True)


@login_required
def download(request, path):
    return _download(request, path)


def shared_download(request, slug, token, path):
    _checked_shared_album(slug, token)
    return _download(request, path)


def shared_thumbnail(request, slug, token, size_fit, path):
    _checked_shared_album(slug, token)
    return _private_thumbnails_unauthed(request, size_fit, path)
