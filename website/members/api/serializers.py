from base64 import b64encode

from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static_file
from django.templatetags.static import static
from django.urls import reverse
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from members.models import Member, Profile
from members.services import member_achievements, member_societies
from thaliawebsite.api.services import create_image_thumbnail_dict
from utils.templatetags.thumbnail import thumbnail


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


class MemberRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'display_name', 'photo', 'avatar',
                  'profile_description', 'birthday', 'starting_year',
                  'programme', 'website', 'membership_type', 'achievements',
                  'societies')

    display_name = serializers.SerializerMethodField('_display_name')
    photo = serializers.SerializerMethodField('_b64_photo')
    avatar = serializers.SerializerMethodField('_avatar')
    profile_description = serializers.SerializerMethodField(
            '_profile_description')
    birthday = serializers.SerializerMethodField('_birthday')
    starting_year = serializers.SerializerMethodField('_starting_year')
    programme = serializers.SerializerMethodField('_programme')
    website = serializers.SerializerMethodField('_website')
    membership_type = serializers.SerializerMethodField('_membership_type')
    achievements = serializers.SerializerMethodField('_achievements')
    societies = serializers.SerializerMethodField('_societies')

    def _display_name(self, instance):
        return instance.profile.display_name()

    def _profile_description(self, instance):
        return instance.profile.profile_description

    def _birthday(self, instance):
        if instance.profile.show_birthday:
            return instance.profile.birthday
        return None

    def _starting_year(self, instance):
        return instance.profile.starting_year

    def _programme(self, instance):
        return instance.profile.programme

    def _website(self, instance):
        return instance.profile.website

    def _membership_type(self, instance):
        membership = instance.current_membership
        if membership:
            return membership.type
        return None

    def _achievements(self, instance):
        return member_achievements(instance)

    def _societies(self, instance):
        return member_societies(instance)

    def _b64_photo(self, instance):
        if instance.profile.photo:
            photo = ''.join(
                    ['data:image/jpeg;base64,',
                     b64encode(instance.profile.photo.file.read()).decode()])
        else:
            filename = find_static_file('members/images/default-avatar.jpg')
            with open(filename, 'rb') as f:
                photo = ''.join(['data:image/jpeg;base64,',
                                 b64encode(f.read()).decode()])

        return photo

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))
        file = None
        if instance.profile.photo:
            file = instance.profile.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class MemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'display_name', 'photo', 'avatar')

    display_name = serializers.SerializerMethodField('_display_name')
    photo = serializers.SerializerMethodField('_photo')
    avatar = serializers.SerializerMethodField('_avatar')

    def _display_name(self, instance):
        return instance.profile.display_name()

    def _photo(self, instance):
        if instance.profile.photo:
            return self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo,
                          settings.THUMBNAIL_SIZES['medium'],
                          1))
        else:
            return self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
            static('members/images/default-avatar.jpg'))
        file = None
        if instance.profile.photo:
            file = instance.profile.photo
        return create_image_thumbnail_dict(
            self.context['request'], file, placeholder=placeholder,
            size_large='800x800')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('email', 'first_name', 'last_name', 'address_street',
                  'address_street2', 'address_postal_code', 'address_city',
                  'phone_number', 'show_birthday', 'website', 'photo',
                  'emergency_contact', 'emergency_contact_phone_number',
                  'profile_description', 'nickname', 'display_name_preference',
                  'language', 'receive_optin', 'receive_newsletter')

    email = serializers.SerializerMethodField('_email')
    first_name = serializers.SerializerMethodField('_first_name')
    last_name = serializers.SerializerMethodField('_last_name')

    def _email(self, instance):
        return instance.user.email

    def _first_name(self, instance):
        return instance.user.first_name

    def _last_name(self, instance):
        return instance.user.last_name


class SentryIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'first_name', 'last_name', 'email', 'is_superuser')
