from django.contrib.auth.decorators import login_required
from django.conf import settings

from sendfile import sendfile
import os

from .snippets import sanitize_path


@login_required
def private_thumbnails(request, size_fit, path):
    # TODO do a bit more error handling if the path does not exist?
    # 'path' is supplied as a URL parameter, so treat with care!
    path = sanitize_path(path)
    path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', size_fit, path)
    return sendfile(request, path)
