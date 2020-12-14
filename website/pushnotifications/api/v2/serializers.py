"""Serializers for the pushnotifications app"""
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from pushnotifications.models import Device, Category, Message


class DeviceSerializer(ModelSerializer):
    """Device serializer"""

    class Meta:
        """Meta for the serializer"""

        model = Device
        fields = (
            "pk",
            "registration_id",
            "active",
            "date_created",
            "type",
            "receive_category",
        )
        read_only_fields = (
            "pk",
            "date_created",
        )

        extra_kwargs = {"active": {"default": True}}

    def get_fields(self):
        f = super().get_fields()
        return f

    receive_category = ManyRelatedField(
        allow_empty=True,
        required=False,
        child_relation=PrimaryKeyRelatedField(
            allow_empty=True, queryset=Category.objects.all(), required=False
        ),
    )


class CategorySerializer(ModelSerializer):
    """Category serializers"""

    class Meta:
        """Meta for the serializer"""

        model = Category
        fields = ("key", "name", "description")


class MessageSerializer(ModelSerializer):
    class Meta:
        """Meta for the serializer"""

        model = Message
        fields = ("pk", "title", "body", "url", "category", "sent")
