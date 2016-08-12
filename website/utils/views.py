from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings

from sendfile import sendfile
import os

from .snippets import sanitize_path


def _private_thumbnails_unauthed(request, size_fit, path):
    """This layer of indirection makes it possible to make exceptions
    to the authentication requirements for thumbnails, e.g. when sharing
    photo albums with external parties using access tokens."""
    path = sanitize_path(path)
    path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', size_fit, path)
    if not os.path.isfile(path):
        raise Http404("Thumbnail not found.")
    return sendfile(request, path)


@login_required
def private_thumbnails(request, size_fit, path):
    return _private_thumbnails_unauthed(request, size_fit, path)
