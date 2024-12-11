from announcements.services import close_announcement
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST


@require_POST
def close_announcement_view(request):
    """Close an announcement.

    :param: request
    :return: Http 204 No Content if successful
    """
    if "id" not in request.POST:
        return HttpResponseBadRequest("no id specified")
    try:
        announcement_id = int(request.POST["id"])
    except ValueError:
        return HttpResponseBadRequest("no integer id specified")

    close_announcement(request, announcement_id)
    return HttpResponse(status=204)  # 204: No Content
