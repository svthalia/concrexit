from django.templatetags.static import static
from django.urls import reverse
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from members.models import Member, Profile
from members.services import member_achievements, member_societies
from thaliawebsite.api.services import create_image_thumbnail_dict


class MemberBirthdaySerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Member

    def _start(self, instance):
        return instance.profile.birthday

    def _end(self, instance):
        pass

    def _all_day(self, instance):
        return True

    def _is_birthday(self, instance):
        return True

    def _url(self, instance):
        return reverse('members:profile', kwargs={'pk': instance.pk})

    def _title(self, instance):
        return instance.profile.display_name()

    def _description(self, instance):
        membership = instance.current_membership
        if membership and membership.type == 'honorary':
            return membership.get_type_display()
        return ''

    def _background_color(self, instance):
        membership = instance.current_membership
        if membership and membership.type == 'honorary':
            return '#E62272'
        return 'black'

    def _text_color(self, instance):
        return 'white'


class ProfileRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('pk', 'display_name', 'avatar', 'profile_description',
                  'birthday', 'starting_year', 'programme', 'website',
                  'membership_type', 'achievements', 'societies')

    pk = serializers.SerializerMethodField('_pk')
    avatar = serializers.SerializerMethodField('_avatar')
    birthday = serializers.SerializerMethodField('_birthday')
    membership_type = serializers.SerializerMethodField('_membership_type')
    achievements = serializers.SerializerMethodField('_achievements')
    societies = serializers.SerializerMethodField('_societies')

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
        placeholder = self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))
        file = None
        if instance.photo:
            file = instance.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class MemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'display_name', 'avatar')

    display_name = serializers.SerializerMethodField('_display_name')
    avatar = serializers.SerializerMethodField('_avatar')

    def _display_name(self, instance):
        return instance.profile.display_name()

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
            static('members/images/default-avatar.jpg'))
        file = None
        if instance.profile.photo:
            file = instance.profile.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class ProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('pk', 'email', 'first_name', 'last_name', 'address_street',
                  'address_street2', 'address_postal_code', 'address_city',
                  'phone_number', 'show_birthday', 'website', 'photo',
                  'emergency_contact', 'emergency_contact_phone_number',
                  'profile_description', 'nickname', 'display_name_preference',
                  'language', 'receive_optin', 'receive_newsletter',
                  'display_name', 'avatar', 'birthday', 'starting_year',
                  'programme', 'membership_type', 'achievements', 'societies')

        read_only_fields = ('display_name', 'starting_year', 'programme',
                            'birthday')

    pk = serializers.SerializerMethodField('_pk')
    email = serializers.SerializerMethodField('_email')
    first_name = serializers.SerializerMethodField('_first_name')
    last_name = serializers.SerializerMethodField('_last_name')
    avatar = serializers.SerializerMethodField('_avatar')
    membership_type = serializers.SerializerMethodField('_membership_type')
    achievements = serializers.SerializerMethodField('_achievements')
    societies = serializers.SerializerMethodField('_societies')

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
        placeholder = self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))
        file = None
        if instance.photo:
            file = instance.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class SentryIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'first_name', 'last_name', 'email', 'is_superuser')
