from rest_framework import filters

from members.models import Membership


class StartingYearFilter(filters.BaseFilterBackend):
    """Allows you to filter by starting year."""

    def filter_queryset(self, request, queryset, view):
        starting_year = request.query_params.get("starting_year", None)

        if starting_year:
            queryset = queryset.filter(profile__starting_year=starting_year)

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "starting_year",
                "required": False,
                "in": "query",
                "description": "Filter by starting year",
                "schema": {"type": "number",},
            }
        ]


class MembershipTypeFilter(filters.BaseFilterBackend):
    """Allows you to filter by membership type."""

    def filter_queryset(self, request, queryset, view):
        membership_type = request.query_params.get("membership_type", None)

        if membership_type:
            memberships = Membership.objects.filter(type=membership_type)
            queryset = queryset.filter(pk__in=memberships.values("user__pk"))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "membership_type",
                "required": False,
                "in": "query",
                "description": "Filter by membership type",
                "schema": {"type": "string",},
            }
        ]
