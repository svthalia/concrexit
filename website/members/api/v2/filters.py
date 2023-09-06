from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from rest_framework import filters, serializers

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
                "schema": {
                    "type": "number",
                },
            }
        ]


class FormerMemberFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        former = request.query_params.get("former", "false")

        if former == "false":
            # Filter out former members
            return (
                queryset.exclude(membership=None)
                .filter(
                    Q(membership__until__isnull=True)
                    | Q(membership__until__gt=timezone.now().date())
                )
                .distinct()
            )
        elif former == "true":
            # Filter out current members

            memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
            members_query = ~Q(id=None)

            # Filter out all current active memberships
            memberships_query &= Q(type=Membership.MEMBER) | Q(type=Membership.HONORARY)
            memberships = Membership.objects.filter(memberships_query)
            members_query &= ~Q(pk__in=memberships.values("user__pk"))

            memberships_query = Q(type=Membership.MEMBER) | Q(type=Membership.HONORARY)
            memberships = Membership.objects.filter(memberships_query)
            all_memberships = Membership.objects.all()
            # Only keep members that were once members, or are legacy users
            # that do not have any memberships at all
            members_query &= Q(pk__in=memberships.values("user__pk")) | ~Q(
                pk__in=all_memberships.values("user__pk")
            )

            return queryset.filter(members_query)
        elif former == "any":
            # Include both former and current members
            return queryset
        else:
            raise serializers.ValidationError("invalid former parameter")

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "former",
                "required": False,
                "in": "query",
                "description": "Include former members or only former members",
                "schema": {
                    "type": "string",
                    "enum": ["true", "false", "any"],
                },
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
                "schema": {
                    "type": "string",
                },
            }
        ]
