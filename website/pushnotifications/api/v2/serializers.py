"""Serializers for the pushnotifications app."""
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField

from pushnotifications.models import Category, Device, Message
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class DeviceSerializer(CleanedModelSerializer):
    """Device serializer."""

    class Meta:
        """Meta for the serializer."""

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


class CategorySerializer(CleanedModelSerializer):
    """Category serializers."""

    class Meta:
        """Meta for the serializer."""

        model = Category
        fields = ("key", "name", "description")


class MessageSerializer(CleanedModelSerializer):
    class Meta:
        """Meta for the serializer."""

        model = Message
        fields = ("pk", "title", "body", "url", "category", "sent")
