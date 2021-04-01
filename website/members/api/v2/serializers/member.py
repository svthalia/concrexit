from rest_framework import serializers

from members.api.v2.serializers.profile import ProfileSerializer
from members.models import Member
from members.services import member_achievements, member_societies


class MemberSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        detailed = kwargs.pop("detailed", True)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if not detailed:
            hidden_fields = {"achievements", "societies"}
            existing = set(self.fields.keys())
            for field_name in existing & hidden_fields:
                self.fields.pop(field_name)

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

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile")
        instance.profile = self.fields["profile"].update(
            instance=instance.profile, validated_data=profile_data
        )
        return instance


class MemberListSerializer(MemberSerializer):
    class Meta:
        model = Member
        fields = (
            "pk",
            "membership_type",
            "profile",
        )


class MemberCurrentSerializer(MemberSerializer):
    class Meta:
        model = Member
        fields = ("pk", "membership_type", "profile", "achievements", "societies")

    profile = ProfileSerializer(
        fields=(
            "photo",
            "display_name",
            "short_display_name",
            "programme",
            "starting_year",
            "birthday",
            "show_birthday",
            "website",
            "profile_description",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
            "phone_number",
            "website",
            "emergency_contact",
            "emergency_contact_phone_number",
            "profile_description",
            "nickname",
            "initials",
            "display_name_preference",
            "receive_optin",
            "receive_newsletter",
            "receive_magazine",
            "email_gsuite_only",
        ),
        force_show_birthday=True,
    )
