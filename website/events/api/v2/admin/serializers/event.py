from rest_framework import serializers

from activemembers.api.v2.serializers.member_group import MemberGroupSerializer
from activemembers.models import MemberGroup
from announcements.api.v2.serializers import SlideSerializer
from announcements.models import Slide
from documents.api.v2.serializers.document import DocumentSerializer
from documents.models import Document
from events.models import Event
from thaliawebsite.api.v2.serializers.html import CleanedHTMLSerializer


class EventAdminSerializer(serializers.ModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = "__all__"

    description = CleanedHTMLSerializer()
    price = serializers.DecimalField(max_digits=5, decimal_places=2,)
    fine = serializers.DecimalField(max_digits=5, decimal_places=2,)

    def to_internal_value(self, data):
        self.fields["organiser"] = serializers.PrimaryKeyRelatedField(
            queryset=MemberGroup.active_objects.all()
        )
        self.fields["slide"] = serializers.PrimaryKeyRelatedField(
            queryset=Slide.objects.all()
        )
        self.fields["documents"] = serializers.PrimaryKeyRelatedField(
            queryset=Document.objects.all(), many=True
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["organiser"] = MemberGroupSerializer(read_only=True)
        self.fields["slide"] = SlideSerializer(read_only=True)
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
            "organiser",
            "slide",
        )

    description = CleanedHTMLSerializer()
    organiser = MemberGroupSerializer()
    price = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    fine = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
