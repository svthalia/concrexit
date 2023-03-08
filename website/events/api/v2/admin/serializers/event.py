from rest_framework import serializers

from activemembers.api.v2.serializers.member_group import MemberGroupSerializer
from activemembers.models import MemberGroup
from documents.api.v2.serializers.document import DocumentSerializer
from documents.models import Document
from events.models import Event
from payments.api.v2.serializers.payment_amount import PaymentAmountSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from thaliawebsite.api.v2.serializers.html import CleanedHTMLSerializer


class EventAdminSerializer(CleanedModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = "__all__"

    description = CleanedHTMLSerializer()
    price = PaymentAmountSerializer()
    fine = PaymentAmountSerializer()
    mark_present_url = serializers.ReadOnlyField()

    def to_internal_value(self, data):
        self.fields["organisers"] = serializers.PrimaryKeyRelatedField(
            queryset=MemberGroup.active_objects.all()
        )
        self.fields["documents"] = serializers.PrimaryKeyRelatedField(
            queryset=Document.objects.all(), many=True
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["organisers"] = MemberGroupSerializer(many=True, read_only=True)
        self.fields["documents"] = DocumentSerializer(many=True, read_only=True)
        return super().to_representation(instance)


class EventListAdminSerializer(serializers.ModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = (
            "pk",
            "title",
            "description",
            "caption",
            "start",
            "end",
            "category",
            "published",
            "registration_start",
            "registration_end",
            "cancel_deadline",
            "optional_registrations",
            "location",
            "price",
            "fine",
            "max_participants",
            "has_fields",
            "tpay_allowed",
            "organisers",
        )

    description = CleanedHTMLSerializer()
    organisers = MemberGroupSerializer(many=True)
    price = PaymentAmountSerializer()
    fine = PaymentAmountSerializer()
