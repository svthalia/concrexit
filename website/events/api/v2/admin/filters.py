from distutils.util import strtobool

from rest_framework import filters


class PublishedFilter(filters.BaseFilterBackend):
    """Allows you to filter by published status."""

    def filter_queryset(self, request, queryset, view):
        published = request.query_params.get("published", None)

        if published is not None:
            queryset = queryset.filter(published=strtobool(published))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "published",
                "required": False,
                "in": "query",
                "description": "Filter by published status",
                "schema": {"type": "boolean",},
            }
        ]


class EventRegistrationCancelledFilter(filters.BaseFilterBackend):
    """Allows you to filter by event registration status."""

    def filter_queryset(self, request, queryset, view):
        cancelled = request.query_params.get("cancelled", None)

        if cancelled is None:
            return queryset

        if strtobool(cancelled):
            return queryset.exclude(date_cancelled=None)

        return queryset.filter(date_cancelled=None)

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "cancelled",
                "required": False,
                "in": "query",
                "description": "Filter by event registration status",
                "schema": {"type": "boolean",},
            }
        ]
