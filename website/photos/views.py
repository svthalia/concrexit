from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from .models import Album

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
def download(request, filename):
    # TODO actually send the photo that is request for download
    pass
