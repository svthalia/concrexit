from rest_framework import serializers

from activemembers.api.v2.serializers.member_group_membership import (
    MemberGroupMembershipSerializer,
)
from activemembers.models import MemberGroup
from thaliawebsite.api.v2.serializers import ThumbnailSerializer


class MemberGroupSerializer(serializers.ModelSerializer):
    """API serializer for member groups."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "get_memberships" not in self.context and "members" in self.fields:
            self.fields.pop("members")

    class Meta:
        """Meta class for the serializer."""

        model = MemberGroup
        fields = (
            "pk",
            "name",
            "type",
            "since",
            "until",
            "contact_address",
            "photo",
            "members",
        )

    members = serializers.SerializerMethodField("_members")
    type = serializers.SerializerMethodField("_type")
    photo = ThumbnailSerializer(placeholder="activemembers/images/placeholder.png")

    def _members(self, instance):
        memberships = self.context["get_memberships"](instance).prefetch_related(
            "member__membergroupmembership_set"
        )
        return MemberGroupMembershipSerializer(
            many=True, context=self.context
        ).to_representation(memberships)

    def _type(self, instance):
        if hasattr(instance, "board"):
            return "board"
        if hasattr(instance, "committee"):
            return "committee"
        if hasattr(instance, "society"):
            return "society"
        return None


class MemberGroupListSerializer(MemberGroupSerializer):
    class Meta:
        """Meta class for the serializer."""

        model = MemberGroup
        fields = ("pk", "name", "type", "since", "until", "contact_address", "photo")
