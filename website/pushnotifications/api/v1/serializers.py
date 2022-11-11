from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField

from pushnotifications.models import Category, Device, Message
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class DeviceSerializer(CleanedModelSerializer):

    receive_category = ManyRelatedField(
        allow_empty=True,
        required=False,
        child_relation=PrimaryKeyRelatedField(
            allow_empty=True, queryset=Category.objects.all(), required=False
        ),
    )

    class Meta:
        model = Device

        fields = (
            "pk",
            "registration_id",
            "active",
            "date_created",
            "type",
            "receive_category",
        )
        read_only_fields = ("date_created",)

        extra_kwargs = {"active": {"default": True}}


class CategorySerializer(CleanedModelSerializer):
    class Meta:
        model = Category

        fields = ("key", "name", "description")


class MessageSerializer(CleanedModelSerializer):
    class Meta:
        model = Message

        fields = ("pk", "title", "body", "url", "category", "sent")
