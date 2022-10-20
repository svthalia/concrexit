from django.utils.translation import get_language_from_request

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)

from pushnotifications.api.v2.filters import CategoryFilter
from pushnotifications.api.v2.permissions import IsAuthenticatedOwnerOrReadOnly
from pushnotifications.api.v2.serializers import (
    CategorySerializer,
    DeviceSerializer,
    MessageSerializer,
)
from pushnotifications.models import Category, Device, Message
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class DeviceListView(ListAPIView, CreateAPIView):
    """Returns an overview of all devices that are owner by the user."""

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()
    required_scopes_per_method = {
        "GET": ["pushnotifications:read"],
        "POST": ["pushnotifications:write"],
    }

    def get_queryset(self):
        if self.request.user:
            return Device.objects.filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        language = get_language_from_request(self.request)

        try:
            serializer.instance = Device.objects.get(
                user=self.request.user,
                registration_id=serializer.validated_data["registration_id"],
            )
        except Device.DoesNotExist:
            pass

        data = serializer.validated_data
        categories = [c.pk for c in Category.objects.all()]
        if "receive_category" in data and len(data["receive_category"]) > 0:
            categories = data["receive_category"] + ["general"]

        serializer.save(
            user=self.request.user, language=language, receive_category=categories
        )


class DeviceDetailView(RetrieveAPIView, UpdateAPIView):
    """Returns details of a device."""

    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        IsAuthenticatedOwnerOrReadOnly,
    ]
    serializer_class = DeviceSerializer
    required_scopes = ["pushnotifications:read", "pushnotifications:write"]
    queryset = Device.objects.all()

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class CategoryListView(ListAPIView):
    """Returns an overview of all available categories for push notifications."""

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    required_scopes = ["pushnotifications:read"]


class MessageListView(ListAPIView):
    """Returns a list of message sent to the user."""

    serializer_class = MessageSerializer
    required_scopes = ["pushnotifications:read"]
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    filter_backends = (OrderingFilter, CategoryFilter)
    ordering_fields = ("sent",)

    def get_queryset(self):
        if self.request.user:
            return Message.all_objects.filter(users=self.request.user)
        return Message.all_objects.all()


class MessageDetailView(RetrieveAPIView):
    """Returns a message."""

    serializer_class = MessageSerializer
    required_scopes = ["pushnotifications:read"]
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]

    def get_queryset(self):
        if self.request.user:
            return Message.all_objects.filter(users=self.request.user)
        return Message.all_objects.all()
