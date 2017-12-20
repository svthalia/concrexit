from base64 import b64encode

from django.contrib.staticfiles.finders import find as find_static_file
from django.templatetags.static import static
from django.urls import reverse
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from members.models import Member
from members.services import member_achievements
from thaliawebsite.settings import settings
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
                  'programme', 'website', 'membership_type', 'achievements')

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
        data = {
            'full': placeholder,
            'small': placeholder,
            'medium': placeholder,
            'large': placeholder,
        }
        if instance.profile.photo:
            data['full'] = self.context['request'].build_absolute_uri(
                '%s%s' % (settings.MEDIA_URL, instance.profile.photo))
            data['small'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '110x110', 1))
            data['medium'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '220x220', 1))
            data['large'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '800x800', 1))
        return data


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
                thumbnail(instance.profile.photo, '220x220', 1))
        else:
            return self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))

    def _avatar(self, instance):
        placeholder = self.context['request'].build_absolute_uri(
                static('members/images/default-avatar.jpg'))
        data = {
            'full': placeholder,
            'small': placeholder,
            'medium': placeholder,
            'large': placeholder,
        }
        if instance.profile.photo:
            data['full'] = self.context['request'].build_absolute_uri(
                '%s%s' % (settings.MEDIA_URL, instance.profile.photo))
            data['small'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '110x110', 1))
            data['medium'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '220x220', 1))
            data['large'] = self.context['request'].build_absolute_uri(
                thumbnail(instance.profile.photo, '800x800', 1))
        return data
