from datetime import datetime

from django.utils import timezone
from pytz.exceptions import InvalidTimeError
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, \
    IsAuthenticated
from rest_framework.response import Response

from partners.api.serializers import PartnerEventCalendarJSSerializer, \
    PartnerEventSerializer, PartnerSerializer
from partners.models import Partner, PartnerEvent


def _extract_date(param):
    """Extract the date from an arbitrary string"""
    if param is None:
        return None
    try:
        return timezone.make_aware(datetime.strptime(param, '%Y-%m-%dT%H:%M:%S'))
    except ValueError:
        return timezone.make_aware(datetime.strptime(param, '%Y-%m-%d'))


def _extract_date_range(request):
    """Extract a date range from an arbitrary string"""
    try:
        start = _extract_date(request.query_params['start'])
        end = _extract_date(request.query_params['end'])
    except (ValueError, KeyError, InvalidTimeError) as e:
        raise ParseError(detail='start or end query parameters invalid') from e
    return end, start


class PartnerViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)

    @action(detail=False, permission_classes=(IsAuthenticatedOrReadOnly,))
    def calendarjs(self, request):
        end, start = _extract_date_range(request)

        queryset = PartnerEvent.objects.filter(
            end__gte=start,
            start__lte=end,
            published=True
        )

        serializer = PartnerEventCalendarJSSerializer(queryset, many=True)
        return Response(serializer.data)


class PartnerEventViewset(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerEvent.objects.filter(end__gte=timezone.now(),
                                           published=True)
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('start', 'end')
    serializer_class = PartnerEventSerializer
