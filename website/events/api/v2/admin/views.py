import json

from django.http import HttpResponse, Http404
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework import filters as framework_filters

from events import services
from events.api.v2.admin import filters
from events.api.v2.admin.permissions import IsOrganiser
from events.api.v2.admin.serializers.event import (
    EventListAdminSerializer,
    EventAdminSerializer,
)
from events.api.v2.admin.serializers.event_registration import (
    EventRegistrationAdminSerializer,
)
from events.models import Event, EventRegistration
from thaliawebsite.api.v2.admin.views import (
    AdminListAPIView,
    AdminRetrieveAPIView,
    AdminCreateAPIView,
    AdminUpdateAPIView,
    AdminDestroyAPIView,
    AdminPermissionsMixin,
)
import events.api.v2.filters as normal_filters


class EventAdminListCreateAPIView(AdminListAPIView, AdminCreateAPIView):
    queryset = Event.objects.prefetch_related("organiser")
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:admin"]
    filter_backends = [
        framework_filters.OrderingFilter,
        normal_filters.CategoryFilter,
        normal_filters.OrganiserFilter,
        normal_filters.EventDateFilter,
        filters.PublishedFilter,
    ]
    ordering_fields = (
        "start",
        "end",
        "published",
        "registration_start",
        "registration_end",
    )

    def get_serializer_class(self):
        if self.request.method.lower() == "post":
            return EventAdminSerializer
        return EventListAdminSerializer


class EventAdminDetailAPIView(
    AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    queryset = Event.objects.all()
    serializer_class = EventAdminSerializer
    permission_classes = [IsOrganiser, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:admin"]


class EventRegistrationAdminListView(AdminListAPIView, AdminCreateAPIView):
    """Returns a list of registrations."""

    serializer_class = EventRegistrationAdminSerializer
    permission_classes = [IsOrganiser, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:admin"]
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.EventRegistrationCancelledFilter,
    )
    ordering_fields = ("queue_position", "date", "date_cancelled")

    def get_queryset(self):
        event = get_object_or_404(Event, pk=self.kwargs.get("pk"))
        if event:
            return EventRegistration.objects.filter(event_id=event).prefetch_related(
                "member", "member__profile"
            )
        return EventRegistration.objects.none()


class EventRegistrationAdminDetailView(
    AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    """Returns details of an event registration."""

    serializer_class = EventRegistrationAdminSerializer
    queryset = EventRegistration.objects.all()
    permission_classes = [IsOrganiser, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:admin"]
    event_lookup_field = "event_id"

    def get_queryset(self):
        return super().get_queryset().filter(event=self.kwargs["event_id"])


class EventRegistrationAdminFieldsView(AdminPermissionsMixin, APIView):
    """Returns details of an event registration."""

    permission_classes = [IsOrganiser, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["events:admin"]

    def get_object(self):
        event_registration = get_object_or_404(
            EventRegistration,
            event=self.kwargs["event_id"],
            pk=self.kwargs["registration_id"],
        )

        if not event_registration.event.has_fields:
            raise Http404

        return event_registration

    def get(self, request, *args, **kwargs):
        return HttpResponse(
            content=json.dumps(
                services.registration_fields(request, registration=self.get_object())
            ),
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        original = services.registration_fields(request, registration=self.get_object())
        required_keys = set(original.keys()) - set(request.data.keys())
        if len(required_keys) > 0:
            return HttpResponse(
                content=f"Missing keys '{', '.join(required_keys)}' in request",
                status=status.HTTP_400_BAD_REQUEST,
            )
        services.update_registration(
            registration=self.get_object(), field_values=request.data.items()
        )
        return HttpResponse(
            content=json.dumps(
                services.registration_fields(request, registration=self.get_object())
            ),
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        services.update_registration(
            registration=self.get_object(), field_values=request.data.items()
        )
        return HttpResponse(
            content=json.dumps(
                services.registration_fields(request, registration=self.get_object())
            ),
            status=status.HTTP_200_OK,
        )
