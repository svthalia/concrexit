from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import ParseError, PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from pytz.exceptions import InvalidTimeError

from events import services
from events.api.permissions import UnpublishedEventPermissions
from events.api.serializers import (
    EventCalenderJSSerializer,
    UnpublishedEventSerializer,
    EventRetrieveSerializer,
    EventListSerializer,
    RegistrationListSerializer, RegistrationSerializer)
from events.exceptions import RegistrationError
from events.models import Event, Registration


def _extract_date(param):
    if param is None:
        return None
    return timezone.make_aware(datetime.strptime(param, '%Y-%m-%d'))


def _extract_date_range(request):
    try:
        start = _extract_date(request.query_params['start'])
        end = _extract_date(request.query_params['end'])
    except (ValueError, KeyError, InvalidTimeError) as e:
        raise ParseError(detail='start or end query parameters invalid') from e
    return end, start


class EventViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(published=True)
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('start', 'end')

    def get_queryset(self):
        queryset = Event.objects.filter(published=True)

        if self.action == 'retrieve':
            return queryset

        try:
            start = _extract_date(self.request.query_params.get('start', None))
        except (ValueError, InvalidTimeError) as e:
            raise ParseError(detail='start query parameter invalid') from e
        try:
            end = _extract_date(self.request.query_params.get('end', None))
        except (ValueError, InvalidTimeError) as e:
            raise ParseError(detail='end query parameter invalid') from e

        if start is not None:
            queryset = queryset.filter(start__gte=start)
        if end is not None:
            queryset = queryset.filter(end__lte=end)
        if start is None and end is None:
            queryset = queryset.filter(end__gte=timezone.now())

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        if self.action == 'retrieve':
            return EventRetrieveSerializer
        return EventCalenderJSSerializer

    def get_serializer_context(self):
        return super().get_serializer_context()

    @detail_route(methods=['get', 'post'])
    def registrations(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if request.method.lower() == 'post':
            try:
                registration = services.create_registration(
                    request.member, event)
                serializer = RegistrationSerializer(
                    instance=registration,
                    context={'request': request}
                )
                return Response(status=201, data=serializer.data)
            except RegistrationError as e:
                raise PermissionDenied(detail=e)

        status = request.query_params.get('status', None)

        # Make sure you can only access other registrations when you have
        # the permissions to do so
        if not services.is_organiser(request.member, event):
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
                    event=pk, date_cancelled=None)[:event.max_participants]

        serializer = RegistrationListSerializer(queryset, many=True,
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

        serializer = EventCalenderJSSerializer(
                queryset, many=True, context={'member': request.member})
        return Response(serializer.data)

    @list_route(permission_classes=(IsAdminUser, UnpublishedEventPermissions,))
    def unpublished(self, request):
        end, start = _extract_date_range(request)

        queryset = Event.objects.filter(
            end__gte=start,
            start__lte=end,
            published=False
        )

        serializer = UnpublishedEventSerializer(
                queryset, many=True, context={'member': request.member})
        return Response(serializer.data)


class RegistrationViewSet(GenericViewSet, RetrieveModelMixin,
                          UpdateModelMixin):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        instance = super().get_object()
        if (instance.member.pk != self.request.member.pk and
                not services.is_organiser(self.request.member,
                                          instance.event)):
            raise NotFound()

        return instance

    # Always set instance so that OPTIONS call will show the info fields too
    def get_serializer(self, *args, **kwargs):
        if len(args) == 0 and "instance" not in kwargs:
            kwargs["instance"] = self.get_object()
        return super().get_serializer(*args, **kwargs)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        registration = serializer.instance
        services.update_registration(registration.member,
                                     registration.event,
                                     serializer.field_values())
        serializer.information_fields = services.registration_fields(
            registration.member, registration.event)

    def destroy(self, request, pk=None, **kwargs):
        registration = self.get_object()
        try:
            services.cancel_registration(request,
                                         registration.member,
                                         registration.event)
            return Response(status=204)
        except RegistrationError as e:
            raise PermissionDenied(detail=e)
