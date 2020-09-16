from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings

from events import services
from events.api.permissions import UnpublishedEventPermissions
from events.api.serializers import (
    EventsCalenderJSSerializer,
    UnpublishedEventsCalenderJSSerializer,
    EventRetrieveSerializer,
    EventListSerializer,
    EventRegistrationSerializer,
    EventRegistrationAdminListSerializer,
    EventRegistrationListSerializer,
)
from events.exceptions import RegistrationError
from events.models import Event, EventRegistration
from utils.snippets import extract_date_range


class EventViewset(viewsets.ReadOnlyModelViewSet):
    """
    Defines the viewset for events, requires an authenticated user
    and enables ordering on the event start/end.
    """

    queryset = Event.objects.filter(published=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering_fields = ("start", "end")
    search_fields = ("title_en",)

    def get_queryset(self):
        queryset = Event.objects.filter(published=True)

        if (
            self.action == "retrieve"
            or api_settings.SEARCH_PARAM in self.request.query_params
        ):
            return queryset

        start, end = extract_date_range(self.request, allow_empty=True)

        if start is not None:
            queryset = queryset.filter(start__gte=start)
        if end is not None:
            queryset = queryset.filter(end__lte=end)
        if start is None and end is None:
            queryset = queryset.filter(end__gte=timezone.now())

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        if self.action == "retrieve":
            return EventRetrieveSerializer
        return EventsCalenderJSSerializer

    def get_serializer_context(self):
        return super().get_serializer_context()

    @action(detail=True, methods=["get", "post"], permission_classes=(IsAuthenticated,))
    def registrations(self, request, pk):
        """
        Defines a custom route for the event's registrations,
        can filter on registration status if the user is an organiser

        :param request: the request object
        :param pk: the primary key of the event
        :return: the registrations of the event
        """
        event = get_object_or_404(Event, pk=pk)

        if request.method.lower() == "post":
            try:
                registration = services.create_registration(request.member, event)
                serializer = EventRegistrationSerializer(
                    instance=registration, context={"request": request}
                )
                return Response(status=201, data=serializer.data)
            except RegistrationError as e:
                raise PermissionDenied(detail=e)

        status = request.query_params.get("status", None)

        # Make sure you can only access other registrations when you have
        # the permissions to do so
        context = {"request": request}
        if services.is_organiser(self.request.member, event):
            queryset = EventRegistration.objects.filter(event=pk)
            if status == "queued":
                queryset = EventRegistration.objects.filter(
                    event=pk, date_cancelled=None
                )[event.max_participants :]
            elif status == "cancelled":
                queryset = EventRegistration.objects.filter(
                    event=pk, date_cancelled__not=None
                )
            elif status == "registered":
                queryset = EventRegistration.objects.filter(
                    event=pk, date_cancelled=None
                )[: event.max_participants]

            serializer = EventRegistrationAdminListSerializer(
                queryset, many=True, context=context
            )
        else:
            serializer = EventRegistrationListSerializer(
                EventRegistration.objects.filter(event=pk, date_cancelled=None)[
                    : event.max_participants
                ],
                many=True,
                context=context,
            )

        return Response(serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticatedOrReadOnly,))
    def calendarjs(self, request):
        """
        Defines a custom route that outputs the correctly formatted
        events information for CalendarJS, published events only
        :param request: the request object

        :return: response containing the data
        """
        start, end = extract_date_range(request)

        queryset = Event.objects.filter(end__gte=start, start__lte=end, published=True)

        serializer = EventsCalenderJSSerializer(
            queryset, many=True, context={"member": request.member}
        )
        return Response(serializer.data)

    @action(
        detail=False, permission_classes=(IsAdminUser, UnpublishedEventPermissions,)
    )
    def unpublished(self, request):
        """
        Defines a custom route that outputs the correctly formatted
        events information for CalendarJS, unpublished events only

        :param request: the request object
        :return: response containing the data
        """
        start, end = extract_date_range(request)

        queryset = Event.objects.filter(end__gte=start, start__lte=end, published=False)

        serializer = UnpublishedEventsCalenderJSSerializer(
            queryset, many=True, context={"member": request.member}
        )
        return Response(serializer.data)
