import datetime

from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from utils.snippets import datetime_to_lectureyear

from .models import Board, Committee, MemberGroupMembership, Society


class _MemberGroupDetailView(DetailView):
    """Base view for membergroup details."""

    context_object_name = "membergroup"

    def _get_memberships(self, group):
        return MemberGroupMembership.active_objects.filter(group=group)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        memberships = self._get_memberships(context["membergroup"]).prefetch_related(
            "member__membergroupmembership_set"
        )
        members = [
            {
                "member": x.member,
                "chair": x.chair,
                "role": x.role,
                "since": x.initial_connected_membership.since,
                "until": (
                    None
                    if x.latest_connected_membership.until
                    == context["membergroup"].until
                    else x.latest_connected_membership.until
                ),
                "is_board": hasattr(x.group, "board"),
            }
            for x in memberships
        ]

        members.sort(key=lambda x: x["since"])

        context.update({"members": members})
        return context


class CommitteeIndexView(ListView):
    """View that renders the committee overview page."""

    template_name = "activemembers/committee_index.html"
    queryset = Committee.active_objects
    context_object_name = "committees"

    def get_ordering(self) -> str:
        return "name"


class CommitteeDetailView(_MemberGroupDetailView):
    """View that renders the page of one selected committee."""

    template_name = "activemembers/committee_detail.html"
    model = Committee


class SocietyIndexView(ListView):
    """View that renders the societies overview page."""

    template_name = "activemembers/society_index.html"
    queryset = Society.active_objects
    context_object_name = "societies"

    def get_ordering(self) -> str:
        return "name"


class SocietyDetailView(_MemberGroupDetailView):
    """View that renders the page of one selected society."""

    template_name = "activemembers/society_detail.html"
    model = Society


class BoardIndexView(ListView):
    """View that renders the board overview page."""

    template_name = "activemembers/board_index.html"
    context_object_name = "old_boards"
    current_board = None

    def get_queryset(self) -> QuerySet:
        if self.current_board:
            return Board.objects.exclude(pk=self.current_board.pk)
        return Board.objects.all()

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update({"current_board": self.current_board})
        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        lecture_year = datetime_to_lectureyear(datetime.date.today())
        self.current_board = Board.objects.filter(
            since__year=lecture_year, until__year=lecture_year + 1
        ).first()
        return super().dispatch(request, *args, **kwargs)


class BoardDetailView(_MemberGroupDetailView):
    """View that renders the page of one selected board."""

    template_name = "activemembers/board_detail.html"
    context_object_name = "membergroup"

    def _get_memberships(self, group):
        return MemberGroupMembership.objects.filter(group=group)

    def get_object(self, queryset=None) -> Board:
        return get_object_or_404(
            Board,
            since__year=self.kwargs.get("since"),
            until__year=self.kwargs.get("until"),
        )
