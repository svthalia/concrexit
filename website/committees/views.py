from django.shortcuts import render, get_object_or_404

from .models import Committee, CommitteeMembership


def index(request):
    """Overview of committees"""
    committees = Committee.objects.all()

    return render(request,
                  'committees/index.html',
                  {'committees': committees})


def details(request, committee_id):
    """View the details of a committee"""
    committee = get_object_or_404(Committee, pk=committee_id)

    members = []
    memberships = (CommitteeMembership
                   .active_memberships
                   .filter(committee=committee))
    for membership in memberships:
        member = membership.member
        member.chair = membership.chair
        member.committee_since = membership.since
        members.append(member)  # list comprehension would be more pythonic?

    return render(request, 'committees/details.html',
                  {'committee': committee,
                   'members': members})
