"""Utility views."""
from datetime import timedelta

from django.core import signing
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.module_loading import import_string

from django_sendfile import sendfile


def get_thumb_modified_time(storage, path):
    storage_value = cache.get(
        f"thumbnails_{path}", timezone.make_aware(timezone.datetime.min)
    )
    if storage_value.timestamp() <= 0:
        try:
            storage_value = storage.get_modified_time(path)
            cache.set(f"thumbnails_{path}", storage_value, 60 * 60)
        except:  # noqa: E722
            # File probably does not exist
            pass
    return storage_value


def _get_signature_info(request):
    if "sig" in request.GET:
        signature = request.GET.get("sig")
        try:
            return signing.loads(signature, max_age=timedelta(hours=3))
        except BadSignature:
            pass
    raise PermissionDenied


def private_media(request, request_path):
    """Serve private media files.

    :param request: the request
    :return: the media file
    """
    # Get image information from signature
    # raises PermissionDenied if bad signature
    sig_info = _get_signature_info(request)
    storage = import_string(sig_info["storage"])()
    serve_path = sig_info["serve_path"]

    if not storage.exists(serve_path) or not serve_path == request_path:
        # 404 if the file does not exist
        raise Http404("Media not found.")

    # Serve the file, or redirect to a signed bucket url in the case of S3
    if hasattr(storage, "bucket"):
        serve_url = storage.url(sig_info["serve_path"])
        return redirect(
            f"{serve_url}",
            permanent=False,
        )
    return sendfile(
        request,
        serve_path,
        attachment=bool(sig_info.get("attachment", False)),
        attachment_filename=sig_info.get("attachment", None),
    )
