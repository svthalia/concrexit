from rest_framework import serializers

from members.api.v2.serializers.profile import ProfileSerializer
from members.models import Member
from members.services import member_achievements, member_societies


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ("pk", "membership_type", "profile", "achievements", "societies")

    membership_type = serializers.SerializerMethodField("_membership_type")
    profile = ProfileSerializer(
        fields=(
            "photo",
            "display_name",
            "short_display_name",
            "programme",
            "starting_year",
            "birthday",
            "website",
            "profile_description",
        )
    )
    achievements = serializers.SerializerMethodField("_achievements")
    societies = serializers.SerializerMethodField("_societies")

    def _achievements(self, instance):
        return member_achievements(instance)

    def _societies(self, instance):
        return member_societies(instance)

    def _membership_type(self, instance):
        membership = instance.current_membership
        if membership:
            return membership.type
        return None


class MemberListSerializer(MemberSerializer):
    class Meta:
        model = Member
        fields = (
            "pk",
            "membership_type",
            "profile",
        )
