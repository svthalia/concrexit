from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from pushnotifications.api.permissions import IsOwner
from pushnotifications.api.serializers import DeviceSerializer
from pushnotifications.models import Device


class DeviceViewSet(ModelViewSet):
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
                registration_id=serializer.validated_data['registration_id']
            )
        except Device.DoesNotExist:
            pass
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
