from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from partners.api.serializers import (
    PartnerEventCalendarJSSerializer,
    PartnerEventSerializer,
    PartnerSerializer,
)
from partners.models import Partner, PartnerEvent
from utils.snippets import extract_date_range


class PartnerViewset(viewsets.ReadOnlyModelViewSet):
    """View set for partners."""

    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)

    @action(detail=False, permission_classes=(IsAuthenticatedOrReadOnly,))
    def calendarjs(self, request):
        """Return response with serialized partner event calender data."""
        start, end = extract_date_range(request)

        queryset = PartnerEvent.objects.filter(
            end__gte=start, start__lte=end, published=True
        )

        serializer = PartnerEventCalendarJSSerializer(queryset, many=True)
        return Response(serializer.data)


class PartnerEventViewset(viewsets.ReadOnlyModelViewSet):
    """View set for partner events."""

    queryset = PartnerEvent.objects.filter(end__gte=timezone.now(), published=True)
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("start", "end")
    serializer_class = PartnerEventSerializer
