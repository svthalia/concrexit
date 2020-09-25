"""DRF serializers defined by the activemembers package"""
from rest_framework import serializers

from activemembers.models import MemberGroup, MemberGroupMembership
from members.api.serializers import MemberListSerializer


class MemberGroupSerializer(serializers.ModelSerializer):
    """MemberGroup serializer"""

    class Meta:
        """Meta class for the serializer"""

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

    members = MemberListSerializer(many=True)
    chair = serializers.SerializerMethodField("_chair")
    type = serializers.SerializerMethodField("_type")

    def _chair(self, instance):
        membership = (
            MemberGroupMembership.objects.filter(chair=True, group=instance)
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
