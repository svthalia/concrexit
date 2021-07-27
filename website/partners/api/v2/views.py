from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

from partners.api.v2 import filters
from partners.api.v2.serializers.partner import PartnerSerializer
from partners.api.v2.serializers.partner_event import PartnerEventSerializer
from partners.models import PartnerEvent, Partner


class PartnerEventListView(ListAPIView):
    """Returns an overview of all partner events."""

    serializer_class = PartnerEventSerializer
    queryset = PartnerEvent.objects.filter(published=True)
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.PartnerEventDateFilter,
    )
    ordering_fields = ("start", "end", "title")
    search_fields = ("title",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]


class PartnerEventDetailView(RetrieveAPIView):
    """Returns a single partner event."""

    serializer_class = PartnerEventSerializer
    queryset = PartnerEvent.objects.filter(published=True)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]



class PartnerListView(ListAPIView):
    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
    )
    ordering_fields = ("name", "pk")
    search_fields = ("name",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]
