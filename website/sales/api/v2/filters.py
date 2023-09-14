from rest_framework import filters
from rest_framework.exceptions import ValidationError

from utils.snippets import extract_date_range, strtobool


class ShiftActiveFilter(filters.BaseFilterBackend):
    """Allows you to filter by active status."""

    def filter_queryset(self, request, queryset, view):
        active = request.query_params.get("active", None)

        if active is not None:
            try:
                queryset = queryset.filter(active=strtobool(active))
            except ValueError as e:
                raise ValidationError({"active": "Invalid filter value."}) from e

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "active",
                "required": False,
                "in": "query",
                "description": "Filter by active status",
                "schema": {
                    "type": "boolean",
                },
            }
        ]


class ShiftLockedFilter(filters.BaseFilterBackend):
    """Allows you to filter by locked status."""

    def filter_queryset(self, request, queryset, view):
        locked = request.query_params.get("locked", None)

        if locked is not None:
            try:
                queryset = queryset.filter(locked=strtobool(locked))
            except ValueError as e:
                raise ValidationError({"locked": "Invalid filter value."}) from e

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "locked",
                "required": False,
                "in": "query",
                "description": "Filter by locked status",
                "schema": {
                    "type": "boolean",
                },
            }
        ]


class ShiftDateFilter(filters.BaseFilterBackend):
    """Allows you to filter by event start/end dates."""

    def filter_queryset(self, request, queryset, view):
        start, end = extract_date_range(request, allow_empty=True)

        if start is not None:
            queryset = queryset.filter(end__gte=start)
        if end is not None:
            queryset = queryset.filter(start__lte=end)

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "start",
                "required": False,
                "in": "query",
                "description": "Filter shifts by ISO date, starting with this parameter (i.e. 2021-03-30T04:20:00) where `event.end >= value`",
                "schema": {
                    "type": "string",
                },
            },
            {
                "name": "end",
                "required": False,
                "in": "query",
                "description": "Filter shifts by ISO date, ending with this parameter (i.e. 2021-05-16T13:37:00) where `event.start <= value`",
                "schema": {
                    "type": "string",
                },
            },
        ]
