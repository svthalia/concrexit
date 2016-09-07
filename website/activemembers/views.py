from django.shortcuts import render, get_object_or_404

from .models import Committee, CommitteeMembership, Board


def committees(request):
    """Overview of committees"""
    committees = Committee.objects.all()

    return render(request,
                  'activemembers/index.html',
                  {'committees': committees})


def details(request, committee_id):
    """View the details of a committee"""
    committee = get_object_or_404(Committee, pk=committee_id)

    members = []
    memberships = (CommitteeMembership
                   .active_memberships
                   .filter(committee=committee)
                   .prefetch_related('member'))
    for membership in memberships:
        member = membership.member
        member.chair = membership.chair
        member.committee_since = membership.since
        members.append(member)  # list comprehension would be more pythonic?

    return render(request, 'activemembers/details.html',
                  {'committee': committee,
                   'members': members})


def boards(request, id=None):
    """
    View the board pages

    The id is for javascript, and ignored
    """
    boards = Board.objects.all()

    boardmembers = dict()
    for board in boards:
        members = []
        memberships = (CommitteeMembership
                       .objects
                       .filter(committee=board)
                       .prefetch_related('member'))
        for membership in memberships:
            member = membership.member
            member.role = membership.role
            member.chair = membership.chair
            members.append(member)
        boardmembers[board.pk] = members

    return render(request,
                  'activemembers/boards.html',
                  {'boards': boards,
                   'boardmembers': boardmembers,
                   'first_board': boards[0]})
