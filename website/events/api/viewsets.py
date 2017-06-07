from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from events.api.permissions import UnpublishedEventPermissions
from events.api.serializers import (
    EventCalenderJSSerializer,
    UnpublishedEventSerializer,
    EventRetrieveSerializer,
    EventListSerializer,
    RegistrationSerializer)
from events.models import Event, Registration


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


class EventViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(end__gte=timezone.datetime.now(),
                                    published=True)
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('start', 'end')

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        if self.action == 'retrieve':
            return EventRetrieveSerializer
        return EventCalenderJSSerializer

    def get_serializer_context(self):
        return super().get_serializer_context()

    @detail_route()
    def registrations(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        status = request.query_params.get('status', None)

        # Make sure you can only access other registrations when you have
        # the permissions to do so
        if not request.user.has_perm('events.change_event'):
            status = 'registered'
        elif (not request.user.is_superuser and
                not request.user.has_perm('events.override_organiser')):
            committees = request.user.member.get_committees().filter(
                pk=event.organiser.pk).count()
            if committees == 0:
                status = 'registered'

        queryset = Registration.objects.filter(event=pk)
        if status is not None:
            if status == 'queued':
                queryset = Registration.objects.filter(
                    event=pk, date_cancelled=None)[event.max_participants:]
            elif status == 'cancelled':
                queryset = Registration.objects.filter(
                    event=pk, date_cancelled__not=None)
            elif status == 'registered':
                queryset = Registration.objects.filter(
                    event=pk, date_cancelled=None)[event.max_participants:]

        serializer = RegistrationSerializer(queryset, many=True,
                                            context={'request': request})

        return Response(serializer.data)

    @list_route(permission_classes=(IsAuthenticatedOrReadOnly,))
    def calendarjs(self, request):
        end, start = _extract_date_range(request)

        queryset = Event.objects.filter(
            end__gte=start,
            start__lte=end,
            published=True
        )

        serializer = EventCalenderJSSerializer(queryset, many=True,
                                               context={'user': request.user})
        return Response(serializer.data)

    @list_route(permission_classes=(IsAdminUser, UnpublishedEventPermissions,))
    def unpublished(self, request):
        end, start = _extract_date_range(request)

        queryset = Event.objects.filter(
            end__gte=start,
            start__lte=end,
            published=False
        )

        serializer = UnpublishedEventSerializer(queryset, many=True,
                                                context={'user': request.user})
        return Response(serializer.data)
