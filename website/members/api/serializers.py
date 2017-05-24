from django.urls import reverse

from events.api.serializers import CalenderJSSerializer
from members.models import Member

from rest_framework import serializers


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


class MemberSerializer(serializers.ModelSerializer):

    photo = serializers.CharField(source='b64_photo')

    class Meta:
        model = Member

        fields = ('pk', 'display_name', 'photo')
