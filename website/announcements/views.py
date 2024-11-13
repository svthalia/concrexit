from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST


@require_POST
def close_announcement(request):
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

    # if we do not have a list of closed announcements yet:
    if "closed_announcements" not in request.session:
        request.session["closed_announcements"] = []  # cannot use sets here :(
    # duplicates should never occur anyway, but it does not hurt to check
    if announcement_id not in request.session["closed_announcements"]:
        request.session["closed_announcements"].append(announcement_id)
    # needs to be explicitly marked since we only edited an existing object
    request.session.modified = True
    return HttpResponse(status=204)  # 204: No Content
