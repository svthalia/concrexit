from django.db.models import Q
from rest_framework import filters

from activemembers.models import Board, Committee, Society
from utils.snippets import extract_date_range


class MemberGroupTypeFilter(filters.BaseFilterBackend):
    """Allows you to filter by organiser id."""

    def filter_queryset(self, request, queryset, view):
        type = request.query_params.get("type", None)

        if type == "board":
            queryset = queryset.filter(pk__in=Board.active_objects.values("pk"))
        elif type == "committee":
            queryset = queryset.filter(pk__in=Committee.active_objects.values("pk"))
        elif type == "society":
            queryset = queryset.filter(pk__in=Society.active_objects.values("pk"))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "type",
                "required": False,
                "in": "query",
                "description": "Filter by member group type",
                "schema": {"type": "string", "enum": ["board", "committee", "society"]},
            }
        ]


class MemberGroupDateFilter(filters.BaseFilterBackend):
    """Allows you to filter by event start/end dates."""

    def filter_queryset(self, request, queryset, view):
        start, end = extract_date_range(request, allow_empty=True)

        if start is not None:
            queryset = queryset.filter(Q(until__isnull=True) | Q(until__gte=start))
        if end is not None:
            queryset = queryset.filter(Q(since__isnull=True) | Q(since__lte=end))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "start",
                "required": False,
                "in": "query",
                "description": "Filter member groups by ISO date, starting with this parameter (e.g. 2021-03-30T04:20:00) where `group.until >= value`",
                "schema": {"type": "string", "format": "date-time"},
            },
            {
                "name": "end",
                "required": False,
                "in": "query",
                "description": "Filter member groups by ISO date, ending with this parameter (e.g. 2021-05-16T13:37:00) where `group.since <= value`",
                "schema": {"type": "string", "format": "date-time"},
            },
        ]
