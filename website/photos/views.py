from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import Album
from utils.snippets import sanitize_path

from sendfile import sendfile
import os

COVER_FILENAME = 'cover.jpg'


@login_required
def index(request):
    return render(request, 'photos/index.html', {'albums': Album.all()})


@login_required
def album(request, slug):
    for album in Album.all():
        if album.slug == slug:
            break
    else:
        raise Http404(_("Album not found."))
    return render(request, 'photos/album.html', {'album': album})


@login_required
def download(request, path):
    path = sanitize_path(path)
    path = os.path.join(settings.MEDIA_ROOT, 'photos', *path.split('/')[1:])
    if not os.path.isfile(path):
        raise Http404("Photo not found.")
    return sendfile(request, path, attachment=True)
