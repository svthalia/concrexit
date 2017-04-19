from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from events.api.permissions import UnpublishedEventPermissions
from events.api.serializers import EventSerializer, UnpublishedEventSerializer, EventDataSerializer
from events.models import Event


def _extract_date_range(request):
    try:
        start = timezone.make_aware(
            datetime.strptime(request.query_params['start'], '%Y-%m-%d')
        )
        end = timezone.make_aware(
            datetime.strptime(request.query_params['end'], '%Y-%m-%d')
        )
    except:
        raise ParseError(detail='start or end query parameters invalid')
    return end, start


class EventViewset(viewsets.ViewSet):
    queryset = Event.objects.all()

    def list(self, request):
        end, start = _extract_date_range(request)

        queryset = self.queryset.filter(
            end__gte=start,
            start__lte=end,
            published=True
        )

        serializer = EventSerializer(queryset, many=True,
                                     context={'user': request.user})
        return Response(serializer.data)

    @list_route(permission_classes=(IsAdminUser, UnpublishedEventPermissions,))
    def unpublished(self, request):
        end, start = _extract_date_range(request)

        queryset = self.queryset.filter(
            end__gte=start,
            start__lte=end,
            published=False
        )

        serializer = UnpublishedEventSerializer(queryset, many=True,
                                                context={'user': request.user})
        return Response(serializer.data)

    @list_route(permission_classes=[IsAuthenticated])
    def data(self, request):
        if 'event_id' not in request.query_params:
            raise ParseError(detail='missing required event_id parameter')

        try:
            serializer = EventDataSerializer(
                Event.objects.get(pk=request.query_params['event_id'])
            )
            return Response(serializer.data)
        except Event.DoesNotExist:
            raise ParseError(detail='No event with id {}'.format(
                    request.query_params['event_id']
                )
            )
