"""DRF serializers defined by the members package."""
from django.templatetags.static import static

from rest_framework import serializers

from members.models import Member, Profile
from members.services import member_achievements, member_societies
from thaliawebsite.api.services import create_image_thumbnail_dict
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class ProfileRetrieveSerializer(CleanedModelSerializer):
    """Serializer that renders a member profile."""

    class Meta:
        model = Profile
        fields = (
            "pk",
            "display_name",
            "avatar",
            "profile_description",
            "birthday",
            "starting_year",
            "programme",
            "website",
            "membership_type",
            "achievements",
            "societies",
        )

    pk = serializers.SerializerMethodField("_pk")
    avatar = serializers.SerializerMethodField("_avatar")
    birthday = serializers.SerializerMethodField("_birthday")
    membership_type = serializers.SerializerMethodField("_membership_type")
    achievements = serializers.SerializerMethodField("_achievements")
    societies = serializers.SerializerMethodField("_societies")

    def _pk(self, instance):
        return instance.user.pk

    def _birthday(self, instance):
        if instance.show_birthday:
            return instance.birthday
        return None

    def _membership_type(self, instance):
        membership = instance.user.current_membership
        if membership:
            return membership.type
        return None

    def _achievements(self, instance):
        return member_achievements(instance.user)

    def _societies(self, instance):
        return member_societies(instance.user)

    def _avatar(self, instance):
        placeholder = self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )
        file = None
        if instance.photo:
            file = instance.photo
        return create_image_thumbnail_dict(
            file, placeholder=placeholder, size_large="avatar_large"
        )


class MemberListSerializer(serializers.ModelSerializer):
    """Serializer that renders a list of members."""

    class Meta:
        model = Member
        fields = ("pk", "starting_year", "display_name", "membership_type", "avatar")

    display_name = serializers.SerializerMethodField("_display_name")
    starting_year = serializers.SerializerMethodField("_starting_year")
    avatar = serializers.SerializerMethodField("_avatar")
    membership_type = serializers.SerializerMethodField("_membership_type")

    def _display_name(self, instance):
        return instance.profile.display_name()

    def _starting_year(self, instance):
        return instance.profile.starting_year

    def _avatar(self, instance):
        placeholder = self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )
        file = None
        if instance.profile.photo:
            file = instance.profile.photo
        return create_image_thumbnail_dict(
            file, placeholder=placeholder, size_large="avatar_large"
        )

    def _membership_type(self, instance):
        membership = instance.current_membership
        if membership:
            return membership.type
        return None


class ProfileEditSerializer(CleanedModelSerializer):
    """Serializer that renders a profile to be edited."""

    class Meta:
        model = Profile
        fields = (
            "pk",
            "email",
            "first_name",
            "last_name",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
            "phone_number",
            "show_birthday",
            "website",
            "photo",
            "emergency_contact",
            "emergency_contact_phone_number",
            "profile_description",
            "nickname",
            "display_name_preference",
            "receive_optin",
            "receive_newsletter",
            "receive_magazine",
            "display_name",
            "avatar",
            "birthday",
            "starting_year",
            "programme",
            "membership_type",
            "achievements",
            "societies",
        )

        read_only_fields = ("display_name", "starting_year", "programme", "birthday")

    pk = serializers.SerializerMethodField("_pk")
    email = serializers.SerializerMethodField("_email")
    first_name = serializers.SerializerMethodField("_first_name")
    last_name = serializers.SerializerMethodField("_last_name")
    avatar = serializers.SerializerMethodField("_avatar")
    membership_type = serializers.SerializerMethodField("_membership_type")
    achievements = serializers.SerializerMethodField("_achievements")
    societies = serializers.SerializerMethodField("_societies")

    def _pk(self, instance):
        return instance.user.pk

    def _email(self, instance):
        return instance.user.email

    def _first_name(self, instance):
        return instance.user.first_name

    def _last_name(self, instance):
        return instance.user.last_name

    def _membership_type(self, instance):
        membership = instance.user.current_membership
        if membership:
            return membership.type
        return None

    def _achievements(self, instance):
        return member_achievements(instance.user)

    def _societies(self, instance):
        return member_societies(instance.user)

    def _avatar(self, instance):
        placeholder = self.context["request"].build_absolute_uri(
            static("members/images/default-avatar.jpg")
        )
        file = None
        if instance.photo:
            file = instance.photo
        return create_image_thumbnail_dict(
            file, placeholder=placeholder, size_large="avatar_large"
        )
