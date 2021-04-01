from rest_framework import serializers

from activemembers.models import MemberGroupMembership
from members.api.v2.serializers.member import MemberSerializer


class MemberGroupMembershipSerializer(serializers.ModelSerializer):
    """API serializer for member group memberships."""

    class Meta:
        """Meta class for the serializer."""

        model = MemberGroupMembership
        fields = ("member", "chair", "since", "until", "role")

    member = MemberSerializer(detailed=False)
    since = serializers.SerializerMethodField("_since")
    until = serializers.SerializerMethodField("_until")

    def _since(self, instance):
        return instance.initial_connected_membership.since

    def _until(self, instance):
        if instance.latest_connected_membership.until == instance.group.until:
            return None
        return instance.latest_connected_membership.until
