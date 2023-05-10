from django.db.models import Prefetch
from django.utils import timezone

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from events import services
from events.api.v2 import filters
from events.api.v2.serializers.event import EventListSerializer, EventSerializer
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.api.v2.serializers.external_event import ExternalEventSerializer
from events.exceptions import RegistrationError
from events.models import Event, EventRegistration
from events.models.external_event import ExternalEvent
from events.services import is_user_registered
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from thaliawebsite.api.v2.serializers import EmptySerializer


class EventListView(ListAPIView):
    """Returns an overview of all upcoming events."""

    serializer_class = EventListSerializer
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.EventDateFilter,
        filters.CategoryFilter,
        filters.OrganiserFilter,
    )
    ordering_fields = ("start", "end")
    search_fields = ("title",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:read"]

    def get_queryset(self):
        events = (
            Event.objects.filter(published=True)
            .select_related("food_event")
            .select_properties("participant_count")
            .prefetch_related(
                "registrationinformationfield_set",
                "documents",
                "organisers",
                "organisers__board",
                "organisers__committee",
                "organisers__society",
            )
        )
        if self.request.member:
            events = events.prefetch_related(
                Prefetch(
                    "eventregistration_set",
                    to_attr="member_registration",
                    queryset=EventRegistration.objects.filter(
                        member=self.request.member
                    ).select_properties("queue_position"),
                )
            )
        return events


class EventDetailView(RetrieveAPIView):
    """Returns details of an event."""

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:read"]

    def get_queryset(self):
        events = Event.objects.filter(published=True)
        if self.request.member:
            events = events.prefetch_related(
                Prefetch(
                    "eventregistration_set",
                    to_attr="member_registration",
                    queryset=EventRegistration.objects.filter(
                        member=self.request.member
                    ).select_properties("queue_position"),
                )
            )
        return events


class EventRegistrationsView(ListAPIView):
    """Returns a list of registrations."""

    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {
        "GET": ["events:read"],
        "POST": ["events:register"],
        "DELETE": ["events:register"],
    }
    filter_backends = (framework_filters.OrderingFilter,)
    ordering_fields = (
        "date",
        "member",
    )

    def __init__(self):
        super().__init__()
        self.event = None

    def get_serializer_class(self):
        if self.request.method.lower() == "post":
            return EmptySerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.event:
            return EventRegistration.objects.filter(
                event=self.event, date_cancelled=None
            ).select_related("member__profile")[: self.event.max_participants]
        return EventRegistration.objects.none()

    def initial(self, request, *args, **kwargs):
        """Run anything that needs to occur prior to calling the method handler."""
        self.format_kwarg = self.get_format_suffix(**kwargs)

        # Perform content negotiation and store the accepted info on the request
        neg = self.perform_content_negotiation(request)
        request.accepted_renderer, request.accepted_media_type = neg

        # Determine the API version, if versioning is in use.
        version, scheme = self.determine_version(request, *args, **kwargs)
        request.version, request.versioning_scheme = version, scheme

        # Ensure that the incoming request is permitted
        self.perform_authentication(request)

        self.event = get_object_or_404(Event, pk=self.kwargs.get("pk"), published=True)

        self.check_permissions(request)
        self.check_throttles(request)

    def post(self, request, *args, **kwargs):
        try:
            registration = services.create_registration(request.member, self.event)
            serializer = EventRegistrationSerializer(
                instance=registration, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e


class EventRegistrationDetailView(RetrieveAPIView, DestroyAPIView):
    """Returns details of an event registration."""

    serializer_class = EventRegistrationSerializer
    queryset = EventRegistration.objects.all()
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {
        "GET": ["events:read"],
        "DELETE": ["events:register"],
    }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                event=self.kwargs["event_id"],
                event__published=True,
                date_cancelled=None,
            )
        )

    def get_serializer(self, *args, **kwargs):
        if (
            len(args) > 0
            and isinstance(args[0], EventRegistration)
            and args[0].member == self.request.member
        ):
            kwargs.update(
                fields=(
                    "pk",
                    "member",
                    "name",
                    "present",
                    "queue_position",
                    "date",
                    "payment",
                )
            )
        return super().get_serializer(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if self.get_object().member != request.member:
            raise PermissionDenied()

        try:
            services.cancel_registration(request.member, self.get_object().event)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e


class EventRegistrationFieldsView(APIView):
    """Returns details of an event registration."""

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {
        "GET": ["events:read"],
        "PUT": ["events:register"],
        "PATCH": ["events:register"],
    }

    def get_object(self):
        return get_object_or_404(
            EventRegistration,
            event=self.kwargs["event_id"],
            event__published=True,
            pk=self.kwargs["registration_id"],
            member=self.request.member,
        )

    def get(self, request, *args, **kwargs):
        return Response(
            data=services.registration_fields(request, registration=self.get_object()),
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        original = services.registration_fields(request, registration=self.get_object())
        required_keys = set(original.keys()) - set(request.data.keys())
        if len(required_keys) > 0:
            raise ValidationError(
                f"Missing keys '{', '.join(required_keys)}' in request"
            )

        try:
            services.update_registration(
                registration=self.get_object(), field_values=request.data.items()
            )

            return Response(
                data=services.registration_fields(
                    request, registration=self.get_object()
                ),
                status=status.HTTP_200_OK,
            )
        except RegistrationError as e:
            raise ValidationError(e) from e

    def patch(self, request, *args, **kwargs):
        try:
            services.update_registration(
                registration=self.get_object(), field_values=request.data.items()
            )

            return Response(
                data=services.registration_fields(
                    request, registration=self.get_object()
                ),
                status=status.HTTP_200_OK,
            )
        except RegistrationError as e:
            raise ValidationError(e) from e


class ExternalEventListView(ListAPIView):
    """Returns an overview of all partner events."""

    serializer_class = ExternalEventSerializer
    queryset = ExternalEvent.objects.filter(published=True)
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.EventDateFilter,
    )
    ordering_fields = ("start", "end", "title")
    search_fields = ("title",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:read"]


class ExternalEventDetailView(RetrieveAPIView):
    """Returns a single partner event."""

    serializer_class = ExternalEventSerializer
    queryset = ExternalEvent.objects.filter(published=True)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:read"]


class MarkPresentAPIView(APIView):
    """A view that allows uses to mark their presence at an event using a secret token."""

    def patch(self, request, *args, **kwargs):
        """Mark a user as present.

        Checks if the url is correct, the event has not ended yet, and the user is registered.
        """
        event = get_object_or_404(Event, pk=kwargs["pk"])
        if kwargs["token"] != event.mark_present_url_token:
            raise PermissionDenied(detail="Invalid url.")

        if not request.member or not is_user_registered(request.member, event):
            raise PermissionDenied(detail="You are not registered for this event.")

        registration = event.registrations.get(
            member=request.member, date_cancelled=None
        )

        if registration.present:
            return Response(
                data={"detail": "You were already marked as present."},
                status=status.HTTP_200_OK,
            )
        if event.end < timezone.now():
            raise PermissionDenied(
                detail="This event has already ended.",
            )

        registration.present = True
        registration.save()
        return Response(
            data={"detail": "You have been marked as present."},
            status=status.HTTP_200_OK,
        )
