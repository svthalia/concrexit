from events.api.v2.admin.permissions import IsOrganiser
from events.api.v2.admin.serializers.event import EventListSerializer, EventSerializer
from events.models import Event
from thaliawebsite.api.v2.admin.views import (
    AdminListAPIView,
    AdminRetrieveAPIView,
    AdminCreateAPIView,
    AdminUpdateAPIView,
    AdminDestroyAPIView,
)


class EventAdminListAPIView(AdminListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventListSerializer


class EventAdminDetailAPIView(
    AdminRetrieveAPIView, AdminCreateAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsOrganiser]
