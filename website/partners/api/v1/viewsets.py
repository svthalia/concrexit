from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from partners.models import Partner, PartnerEvent
from .serializers import (
    PartnerEventSerializer,
    PartnerSerializer,
)


class PartnerViewset(viewsets.ReadOnlyModelViewSet):
    """View set for partners."""

    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)


class PartnerEventViewset(viewsets.ReadOnlyModelViewSet):
    """View set for partner events."""

    queryset = PartnerEvent.objects.filter(end__gte=timezone.now(), published=True)
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("start", "end")
    serializer_class = PartnerEventSerializer
