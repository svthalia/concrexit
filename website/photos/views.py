from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Album
from utils.snippets import sanitize_path

from sendfile import sendfile
import os

COVER_FILENAME = 'cover.jpg'


@login_required
def index(request):
    albums = sorted(Album.objects.all(), reverse=True)

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
def album(request, pk):
    album = get_object_or_404(Album, pk=int(pk))
    return render(request, 'photos/album.html', {'album': album})


@login_required
def download(request, path):
    path = sanitize_path(path)
    path = os.path.join(settings.MEDIA_ROOT, 'photos', *path.split('/')[1:])
    if not os.path.isfile(path):
        raise Http404("Photo not found.")
    return sendfile(request, path, attachment=True)
