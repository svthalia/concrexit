from rest_framework import filters

from utils.snippets import extract_date_range, strtobool


class CreatedAtFilter(filters.BaseFilterBackend):
    """Allows you to filter by payment creation dates."""

    def filter_queryset(self, request, queryset, view):
        start, end = extract_date_range(request, allow_empty=True)

        if start is not None:
            queryset = queryset.filter(created_at__gte=start)
        if end is not None:
            queryset = queryset.filter(created_at__lte=end)

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "start",
                "required": False,
                "in": "query",
                "description": "Filter payments by ISO date, starting with this parameter (i.e. 2021-03-30T04:20:00) where `payment.created_at >= value`",
                "schema": {
                    "type": "string",
                },
            },
            {
                "name": "end",
                "required": False,
                "in": "query",
                "description": "Filter payments by ISO date, ending with this parameter (i.e. 2021-05-16T13:37:00) where `payment.created_at <= value`",
                "schema": {
                    "type": "string",
                },
            },
        ]


class PaymentTypeFilter(filters.BaseFilterBackend):
    """Allows you to filter by payment type."""

    def filter_queryset(self, request, queryset, view):
        payment_type = request.query_params.get("type", None)

        if payment_type:
            queryset = queryset.filter(type__in=payment_type.split(","))

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "type",
                "required": False,
                "in": "query",
                "description": "Filter by payment type, accepts a comma separated list",
                "schema": {
                    "type": "string",
                },
            }
        ]


class PaymentSettledFilter(filters.BaseFilterBackend):
    """Allows you to filter by settled status."""

    def filter_queryset(self, request, queryset, view):
        settled = request.query_params.get("settled", None)

        if settled is None:
            return queryset
        elif strtobool(settled):
            return queryset.filter(batch__processed=True)
        else:
            return queryset.exclude(batch__processed=True)

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "settled",
                "required": False,
                "in": "query",
                "description": "Filter by settled status",
                "schema": {
                    "type": "boolean",
                },
            }
        ]
