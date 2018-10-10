from django.shortcuts import get_object_or_404, render, redirect, reverse
import datetime
from utils.snippets import datetime_to_lectureyear
from utils.translation import localize_attr_name
from .models import Board, MemberGroupMembership, Committee, Society


def committee_index(request):
    """
    View that renders the committee overview page

    :param request: the request object
    :return: response containing the HTML
    """
    committees = Committee.active_objects.all().order_by(
        localize_attr_name('name'))

    return render(request, 'activemembers/committee_index.html',
                  {'committees': committees})


def committee_detail(request, pk):
    """
    View that renders the page of one selected committee

    :param request: the request object
    :param pk: pk of the selected committee
    :return:
    """
    committee = get_object_or_404(Committee, pk=pk)

    memberships = (MemberGroupMembership
                   .active_objects
                   .filter(group=committee)
                   .prefetch_related('member__membergroupmembership_set'))
    members = [{
        'member': x.member,
        'chair': x.chair,
        'role': x.role,
        'since': x.initial_connected_membership.since
    } for x in memberships]

    members.sort(key=lambda x: x['since'])

    return render(request, 'activemembers/committee_detail.html',
                  {'membergroup': committee,
                   'members': members})


def board_index(request):
    """
    View that renders the board overview page

    :param request: the request object
    :return: response containing the HTML
    """
    current_year = datetime_to_lectureyear(datetime.date.today())
    board = get_object_or_404(
        Board, since__year=current_year, until__year=current_year+1)
    old_boards = Board.objects.all().exclude(pk=board.pk)
    return render(request,
                  'activemembers/board_index.html',
                  {'old_boards': old_boards,
                   'board': board
                   })


def board_detail(request, since, until=None):
    """
    View that renders the board for a specific lecture year

    :param request: the request object
    :param since: xxxx in xxxx-yyyy of the lecture year
    :param until: yyyy in xxxx-yyyy of the lecture year
    :return: response containing the HTML
    """
    if not until:  # try to correct /board/2016 to /2016-2017
        return redirect(reverse('activemembers:board',
                                kwargs={'since': since,
                                        'until': int(since) + 1}))
    board = get_object_or_404(Board, since__year=since, until__year=until)
    memberships = (MemberGroupMembership
                   .objects
                   .filter(group=board)
                   .prefetch_related('member'))

    members = [{
        'member': x.member,
        'chair': x.chair,
        'role': x.role,
    } for x in memberships]

    return render(request, 'activemembers/board_detail.html',
                  {'membergroup': board,
                   'members': members})


def society_index(request):
    """
    View that renders the committee overview page

    :param request: the request object
    :return: response containing the HTML
    """
    societies = Society.active_objects.all().order_by(
        localize_attr_name('name'))

    return render(request, 'activemembers/society_index.html',
                  {'societies': societies})


def society_detail(request, pk):
    """
    View that renders the page of one selected committee

    :param request: the request object
    :param pk: pk of the selected committee
    :return:
    """
    society = get_object_or_404(Society, pk=pk)

    memberships = (MemberGroupMembership
                   .active_objects
                   .filter(group=society)
                   .prefetch_related('member__membergroupmembership_set'))
    members = [{
        'member': x.member,
        'chair': x.chair,
        'role': x.role,
        'since': x.initial_connected_membership.since
    } for x in memberships]

    members.sort(key=lambda x: x['since'])

    return render(request, 'activemembers/society_detail.html',
                  {'membergroup': society,
                   'members': members})
