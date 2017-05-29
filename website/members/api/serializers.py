from base64 import b64encode

from django.contrib.staticfiles.finders import find as find_static_file
from django.urls import reverse
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from members.models import Member
from members.services import member_achievements


class MemberBirthdaySerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Member

    def _start(self, instance):
        return instance.birthday

    def _end(self, instance):
        pass

    def _all_day(self, instance):
        return True

    def _is_birthday(self, instance):
        return True

    def _url(self, instance):
        return reverse('members:profile', kwargs={'pk': instance.pk})

    def _title(self, instance):
        return instance.display_name()

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
        fields = ('pk', 'display_name', 'photo',
                  'birthday', 'starting_year', 'programme',
                  'website', 'membership_type', 'achievements')

    photo = serializers.SerializerMethodField('_b64_photo')
    birthday = serializers.SerializerMethodField('_birthday')
    membership_type = serializers.SerializerMethodField('_membership_type')
    achievements = serializers.SerializerMethodField('_achievements')

    def _birthday(self, instance):
        if instance.show_birthday:
            return instance.birthday
        return None

    def _membership_type(self, instance):
        membership = instance.current_membership
        if membership:
            return membership.type
        return None

    def _achievements(self, instance):
        return member_achievements(instance)

    def _b64_photo(self, instance):
        if instance.photo:
            photo = ''.join(['data:image/jpeg;base64,',
                             b64encode(instance.photo.file.read()).decode()])
        else:
            filename = find_static_file('members/images/default-avatar.jpg')
            with open(filename, 'rb') as f:
                photo = ''.join(['data:image/jpeg;base64,',
                                 b64encode(f.read()).decode()])

        return photo


class MemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'display_name', 'photo',)

    photo = serializers.SerializerMethodField('_b64_photo')

    def _b64_photo(self, instance):
        if instance.photo:
            photo = ''.join(['data:image/jpeg;base64,',
                             b64encode(instance.photo.file.read()).decode()])
        else:
            filename = find_static_file('members/images/default-avatar.jpg')
            with open(filename, 'rb') as f:
                photo = ''.join(['data:image/jpeg;base64,',
                                 b64encode(f.read()).decode()])

        return photo
