from rest_framework import filters


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
