from django.shortcuts import get_object_or_404, render

from .models import Board, Committee, CommitteeMembership


def committee_index(request):
    """Overview of committees"""
    committees = Committee.objects.all()

    return render(request, 'activemembers/committee_index.html',
                  {'committees': committees})


def committee_detail(request, id):
    """View the details of a committee"""
    committee = get_object_or_404(Committee, pk=id)

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

    return render(request, 'activemembers/committee_detail.html',
                  {'committee': committee,
                   'members': members})


def board_index(request):
    boards = Board.objects.all()

    return render(request,
                  'activemembers/board_index.html',
                  {'boards': boards})


def board_detail(request, id):
    """View the details of a committee"""
    board = get_object_or_404(Board, pk=id)

    members = []
    memberships = (CommitteeMembership
                   .active_memberships
                   .filter(committee=board)
                   .prefetch_related('member'))

    for membership in memberships:
        member = membership.member
        member.chair = membership.chair
        member.role = membership.role
        members.append(member)  # list comprehension would be more pythonic?

    return render(request, 'committees/board_detail.html',
                  {'board': board,
                   'members': members})
