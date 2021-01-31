from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from events.api.v2.serializers.event import EventSerializer
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.models import Event, EventRegistration


class EventListView(ListAPIView):
    """Returns an overview of all upcoming events."""

    serializer_class = EventSerializer
    queryset = Event.objects.all()
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering_fields = ("start", "end")
    search_fields = ("title_en",)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["events:read"]


class EventDetailView(RetrieveAPIView):
    """Returns details of a slide."""

    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["events:read"]


class EventRegistrationListView(ListAPIView):

    serializer_class = EventRegistrationSerializer

    def get_queryset(self):
        event = get_object_or_404(Event, pk=self.kwargs.get("pk"))
        return EventRegistration.objects.filter(event=event.pk, date_cancelled=None)[
            : event.max_participants
        ]
