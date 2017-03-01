import hashlib

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from activemembers.models import CommitteeMembership
from members.models import Member

from .models import MailingList


# Consider replacing this completely;
#  - either by a cronjob Python script that queries the database directly
#  - or by a __save__ handler that updates mailman when MailingList changes
#  - or at least by a more nicely separated API with less GET variables
# see issue #29


def index(request):
    if 'apikey' not in request.GET:
        raise PermissionDenied
    apihash = hashlib.sha1(request.GET['apikey'].encode('utf-8')).hexdigest()
    if apihash != 'cb004452d9c80e295bebfc778871b3b082d70ad8':
        raise PermissionDenied
    if 'lists' in request.GET:
        context = {'lists': MailingList.objects.all()}
        return render(request, 'mailinglists/lists.txt', context,
                      content_type='text/plain')
    elif 'list' in request.GET:
        mailinglist = get_object_or_404(MailingList,
                                        pk=int(request.GET['list']))
        return render(request, 'mailinglists/list_data.txt',
                      {'list': mailinglist}, content_type='text/plain')
    elif 'membership_type' in request.GET:
        membership_type = {"Current Members": "member",
                           "Benefactor": "supporter",
                           "Honorary Member": "honorary"
                           }[request.GET['membership_type']]
        members = Member.all_with_membership(membership_type, 'user')
    elif 'custom' in request.GET:
        if request.GET['custom'] == 'commissievoorzitters':
            memberships = (CommitteeMembership.active_memberships
                           .filter(committee__board=False)
                           .filter(chair=True)
                           .prefetch_related('member__user'))
            members = [x.member for x in memberships]
            # The intern is always included; we mock an object with a .email
            members += [{'user': {'email': 'intern@thalia.nu'}}]
        elif request.GET['custom'] == 'optin':
            members = (Member.objects.filter(receive_optin=True)
                                     .prefetch_related('user'))
    try:
        return render(request, 'mailinglists/custom_list.txt',
                      {'members': members}, content_type='text/plain')
    except NameError:
        raise Http404("Insufficient arguments")
