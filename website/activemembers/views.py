import datetime

from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

from utils.snippets import datetime_to_lectureyear
from utils.translation import localize_attr_name
from .models import Board, MemberGroupMembership, Committee, Society


class _MemberGroupDetailView(DetailView):
    """
    Base view for membergroup details
    """
    context_object_name = 'membergroup'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        memberships = (MemberGroupMembership
                       .active_objects
                       .filter(group=context['membergroup'])
                       .prefetch_related('member__membergroupmembership_set'))
        members = [{
            'member': x.member,
            'chair': x.chair,
            'role': x.role,
            'since': x.initial_connected_membership.since
        } for x in memberships]

        members.sort(key=lambda x: x['since'])

        context.update({'members': members})
        return context


class CommitteeIndexView(ListView):
    """
    View that renders the committee overview page
    """
    template_name = 'activemembers/committee_index.html'
    queryset = Committee.active_objects
    context_object_name = 'committees'

    def get_ordering(self) -> str:
        return localize_attr_name('name')


class CommitteeDetailView(_MemberGroupDetailView):
    """
    View that renders the page of one selected committee
    """
    template_name = 'activemembers/committee_detail.html'
    model = Committee


class SocietyIndexView(ListView):
    """
    View that renders the societies overview page
    """
    template_name = 'activemembers/society_index.html'
    queryset = Society.active_objects
    context_object_name = 'societies'

    def get_ordering(self) -> str:
        return localize_attr_name('name')


class SocietyDetailView(_MemberGroupDetailView):
    """
    View that renders the page of one selected society
    """
    template_name = 'activemembers/society_detail.html'
    model = Society


class BoardIndexView(ListView):
    """
    View that renders the board overview page
    """
    template_name = 'activemembers/board_index.html'
    context_object_name = 'old_boards'
    current_board = None

    def get_queryset(self) -> QuerySet:
        if self.current_board:
            return Board.objects.exclude(pk=self.current_board.pk)
        return Board.objects.all()

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update({
            'current_board': self.current_board
        })
        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        lecture_year = datetime_to_lectureyear(datetime.date.today())
        self.current_board = Board.objects.get(
            since__year=lecture_year, until__year=lecture_year + 1)
        return super().dispatch(request, *args, **kwargs)


class BoardDetailView(_MemberGroupDetailView):
    """
    View that renders the page of one selected board
    """
    template_name = 'activemembers/board_detail.html'
    context_object_name = 'membergroup'

    def get_object(self, queryset=None) -> Board:
        return get_object_or_404(
            Board,
            since__year=self.kwargs.get('since'),
            until__year=self.kwargs.get('until')
        )
