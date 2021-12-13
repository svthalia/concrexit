"""DRF serializers defined by the activemembers package."""
from rest_framework import serializers

from activemembers.models import MemberGroup, MemberGroupMembership
from members.api.v1.serializers import MemberListSerializer
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class MemberGroupSerializer(CleanedModelSerializer):
    """MemberGroup serializer."""

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
            "chair",
            "members",
        )

    members = serializers.SerializerMethodField("_members")
    chair = serializers.SerializerMethodField("_chair")
    type = serializers.SerializerMethodField("_type")

    def _members(self, instance):
        memberships = MemberGroupMembership.active_objects.filter(group=instance)
        members = [x.member for x in memberships.select_related("member")]
        return MemberListSerializer(context=self.context, many=True).to_representation(
            members
        )

    def _chair(self, instance):
        membership = (
            MemberGroupMembership.active_objects.filter(chair=True, group=instance)
            .select_related("member")
            .first()
        )
        if membership:
            return MemberListSerializer(context=self.context).to_representation(
                membership.member
            )
        return None

    def _type(self, instance):
        if hasattr(instance, "board"):
            return "board"
        if hasattr(instance, "committee"):
            return "committee"
        if hasattr(instance, "society"):
            return "society"
        return None
