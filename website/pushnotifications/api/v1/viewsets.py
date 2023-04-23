from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from pushnotifications.models import Category, Device, Message

from .permissions import IsOwner
from .serializers import CategorySerializer, DeviceSerializer, MessageSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwner)
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def get_queryset(self):
        # filter all devices to only those belonging to the current user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.instance = Device.objects.get(
                user=self.request.user,
                registration_id=serializer.validated_data["registration_id"],
            )
        except Device.DoesNotExist:
            pass
        data = serializer.validated_data
        if "receive_category" in data and len(data["receive_category"]) > 0:
            categories = data["receive_category"] + ["general"]
            serializer.save(user=self.request.user, receive_category=categories)
        else:
            categories = [c.pk for c in Category.objects.all()]
            serializer.save(user=self.request.user, receive_category=categories)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False)
    def categories(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Message.objects.all()
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("sent",)
    serializer_class = MessageSerializer

    def get_queryset(self):
        queryset = Message.all_objects.filter(
            users=self.request.user, sent__isnull=False
        )

        category = self.request.query_params.get("category", None)
        if category is not None:
            return queryset.filter(category=category)
        return queryset
