from django.shortcuts import render
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required

import os
import re
import random
from datetime import datetime

COVER_FILENAME = 'cover.jpg'


# TODO consider refactoring this to models.py instead, for separation.
def _album_dict(photodir):
    """Creates a dict with album information based on a parent directory."""
    albums = [(name, name.split('_')) for name in os.listdir(photodir)]
    albums = [{'date': datetime.strptime(re.sub(r"\D", "", date), '%Y%m%d'),
               'title': title,
               'name': name,
               } for name, (date, title) in albums]
    for album in albums:
        album['slug'] = slugify('{}-{}'
                                .format(album['date'].strftime('%Y-%m-%d'),
                                        album['title']))
    return albums


@login_required
def index(request):
    photodir = os.path.join(settings.MEDIA_ROOT, 'photos')
    albums = _album_dict(photodir)

    for album in albums:
        albumdir = os.path.join(photodir, album['name'])
        if os.path.isfile(os.path.join(albumdir, COVER_FILENAME)):
            album['cover'] = COVER_FILENAME
        else:
            random.seed(album['name'])
            album['cover'] = random.choice(os.listdir(albumdir))
        album['cover'] = os.path.join('photos',
                                      album['name'],
                                      album['cover'])

    return render(request, 'photos/index.html', {'albums': albums})


@login_required
def album(request, slug):
    photodir = os.path.join(settings.MEDIA_ROOT, 'photos')
    for album in _album_dict(photodir):
        if album['slug'] == slug:
            break
    albumdir = os.path.join(photodir, album['name'])
    photos = [os.path.join('photos', album['name'], photo)
              for photo in os.listdir(albumdir) if photo != COVER_FILENAME]

    return render(request, 'photos/album.html', {'photos': photos})


@login_required
def download(request, filename):
    # TODO actually send the photo that is request for download
    pass
