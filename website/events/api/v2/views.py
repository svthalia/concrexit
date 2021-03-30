from django.http import HttpResponse
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework import filters as framework_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from events import services
from events.api.v2 import filters
from events.api.v2.serializers.event import EventSerializer
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.exceptions import RegistrationError
from events.models import Event, EventRegistration
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from thaliawebsite.api.v2.serializers.empty import EmptySerializer


class EventListView(ListAPIView):
    """Returns an overview of all upcoming events."""

    serializer_class = EventSerializer
    queryset = Event.objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.EventDateFilterBackend
    )
    ordering_fields = ("start", "end")
    search_fields = ("title_en",)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["events:read"]


class EventDetailView(RetrieveAPIView):
    """Returns details of an event."""

    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["events:read"]


class EventRegistrationsView(ListAPIView):
    """Returns a list of registrations."""

    serializer_class = EventRegistrationSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes_per_method = {
        "GET": ["events:read"],
        "POST": ["events:register"],
        "DELETE": ["events:register"],
    }

    def get_serializer_class(self):
        if self.request.method.lower() == "post":
            return EmptySerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return EventRegistration.objects.filter(
            event=self.event.pk, date_cancelled=None
        )[: self.event.max_participants]

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            registration = services.create_registration(request.member, self.event)
            serializer = EventRegistrationSerializer(
                instance=registration, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e

    def delete(self, request, *args, **kwargs):
        try:
            services.cancel_registration(request.member, self.event)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RegistrationError as e:
            raise PermissionDenied(detail=e) from e


class EventRegistrationDetailView(RetrieveAPIView):
    """Returns details of an event registration."""

    serializer_class = EventRegistrationSerializer
    queryset = EventRegistration.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["events:read"]

    def get_queryset(self):
        return super().get_queryset().filter(event=self.kwargs["event_id"])


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
            pk=self.kwargs["registration_id"],
            member=self.request.member,
        )

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
