from django.apps import apps


def get_announcements(request):
    announcements = []
    for app in apps.get_app_configs():
        if hasattr(app, "announcements"):
            announcements += app.announcements(request)
    return announcements


def close_announcement(request, pk):
    """Close an announcement."""
    if "closed_announcements" not in request.session:
        request.session["closed_announcements"] = []  # cannot use sets here :(
    # duplicates should never occur anyway, but it does not hurt to check
    if pk not in request.session["closed_announcements"]:
        request.session["closed_announcements"].append(pk)
    # needs to be explicitly marked since we only edited an existing object
    request.session.modified = True
