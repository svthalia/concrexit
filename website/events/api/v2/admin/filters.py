from django.core.exceptions import ObjectDoesNotExist

from rest_framework import filters

from utils.snippets import strtobool


class PublishedFilter(filters.BaseFilterBackend):
    """Allows you to filter by published status."""

    def filter_queryset(self, request, queryset, view):
        published = request.query_params.get("published", None)

        if published is not None:
            try:
                queryset = queryset.filter(published=strtobool(published))
            except ObjectDoesNotExist:
                raise Exception("Queryset could not be filtered.")

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "published",
                "required": False,
                "in": "query",
                "description": "Filter by published status",
                "schema": {
                    "type": "boolean",
                },
            }
        ]


class EventRegistrationCancelledFilter(filters.BaseFilterBackend):
    """Allows you to filter by event registration cancellation status."""

    def filter_queryset(self, request, queryset, view):
        cancelled = request.query_params.get("cancelled", None)

        if cancelled is None:
            return queryset

        try:
            if strtobool(cancelled):
                return queryset.exclude(date_cancelled=None)
        except ObjectDoesNotExist:
            raise Exception("Queryset could not be filtered.")

        return queryset.filter(date_cancelled=None)

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "cancelled",
                "required": False,
                "in": "query",
                "description": "Filter by event registration cancellation status",
                "schema": {
                    "type": "boolean",
                },
            }
        ]


class EventRegistrationQueuedFilter(filters.BaseFilterBackend):
    """Allows you to filter by event registration by if they're in the queue."""

    def filter_queryset(self, request, queryset, view):
        queued = request.query_params.get("queued", None)

        if queued is None:
            return queryset

        try:
            if strtobool(queued):
                return queryset.exclude(queue_position=None)
        except ObjectDoesNotExist:
            raise Exception("Queryset could not be filtered.")

        return queryset.filter(queue_position=None)

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "queued",
                "required": False,
                "in": "query",
                "description": "Filter by event registration queue position",
                "schema": {
                    "type": "boolean",
                },
            }
        ]
