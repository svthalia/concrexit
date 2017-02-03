from django.http import HttpResponse


def close_announcement(request):
    id = int(request.POST['id'])
    # if we do not have a list of closed announcements yet:
    if 'closed_announcements' not in request.session:
        request.session['closed_announcements'] = []  # cannot use sets here :(
    # duplicates should never occur anyway, but it does not hurt to check
    if id not in request.session['closed_announcements']:
        request.session['closed_announcements'].append(id)
    # needs to be explicitly marked since we only edited an existing object
    request.session.modified = True
    return HttpResponse(status=204)  # 204: No Content
