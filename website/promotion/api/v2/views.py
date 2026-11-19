from django.utils import dateparse

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import ParseError
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from promotion.api.v2.permissions import CanUsePromotionTools
from promotion.api.v2.serializers import PromotionRequestSerializer
from promotion.models import PromotionRequest
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod

STATUSES = {status for status, _ in PromotionRequest.STATUS_TYPES}


class PromotionRequestListView(ListAPIView):
    """Promotion requests ordered by publish date.

    Filters: `start` and `end` (ISO dates, inclusive) on the publish date, and `status`
    (one or more comma-separated statuses, e.g. `not_started,started,finished`).
    Paginated with `limit` and `offset`; follow `next` to get every result.
    """

    serializer_class = PromotionRequestSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope, CanUsePromotionTools]
    required_scopes = ["promotion:read"]

    def get_queryset(self):
        queryset = PromotionRequest.objects.select_related("event", "channel").order_by(
            "publish_date", "pk"
        )
        params = self.request.query_params
        for param, lookup in (("start", "gte"), ("end", "lte")):
            if value := params.get(param):
                try:
                    date = dateparse.parse_date(value)
                except ValueError:
                    date = None
                if date is None:
                    raise ParseError(f"{param} query parameter invalid")
                queryset = queryset.filter(**{f"publish_date__{lookup}": date})
        if value := params.get("status"):
            statuses = set(value.split(","))
            if not statuses <= STATUSES:
                raise ParseError("status query parameter invalid")
            queryset = queryset.filter(status__in=statuses)
        return queryset


class PromotionRequestUpdateView(RetrieveUpdateAPIView):
    """Retrieve a promotion request, or change its status (PATCH {"status": ...})."""

    serializer_class = PromotionRequestSerializer
    queryset = PromotionRequest.objects.select_related("event", "channel")
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        CanUsePromotionTools,
    ]
    required_scopes_per_method = {
        "GET": ["promotion:read"],
        "PATCH": ["promotion:write"],
    }
    http_method_names = ["get", "patch", "options"]
