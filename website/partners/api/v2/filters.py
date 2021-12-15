from rest_framework import filters

from utils.snippets import extract_date_range
from partners.models import VacancyCategory


class PartnerEventDateFilter(filters.BaseFilterBackend):
    """Allows you to filter by partner event start/end dates."""

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
                "description": "Filter events by ISO date, starting with this parameter (i.e. 2021-03-30T04:20:00) where `event.end >= value`",
                "schema": {"type": "string",},
            },
            {
                "name": "end",
                "required": False,
                "in": "query",
                "description": "Filter events by ISO date, ending with this parameter (i.e. 2021-05-16T13:37:00) where `event.start <= value`",
                "schema": {"type": "string",},
            },
        ]


class VacancyPartnerFilter(filters.BaseFilterBackend):
    """Allows you to filter by partner pk."""

    def filter_queryset(self, request, queryset, view):
        partner = request.query_params.get("partner", None)

        if partner is not None:
            queryset = queryset.filter(partner__pk=partner)

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "partner",
                "required": False,
                "in": "query",
                "description": "Filter by partner id",
                "schema": {"type": "number"},
            }
        ]


class VacancyCategoryFilter(filters.BaseFilterBackend):
    """Allows you to filter by category slug."""

    def filter_queryset(self, request, queryset, view):
        categories = request.query_params.get("categories", None)

        if categories:
            queryset = queryset.filter(categories__slug__in=categories.split(","))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "categories",
                "required": False,
                "in": "query",
                "description": "Filter by category slugs, accepts a comma separated list. Return vacancies that have at least one of the specified categories",
                "schema": {"type": "string"},
            }
        ]
