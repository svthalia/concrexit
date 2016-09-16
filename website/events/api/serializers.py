from django.utils import timezone
from django.urls import reverse
from rest_framework import serializers

from events.models import Event


class CalenderJSSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'start', 'end', 'all_day', 'is_birthday',
            'url', 'title', 'description',
            'background_color', 'text_color', 'target_blank'
        )

    start = serializers.SerializerMethodField('_start')
    end = serializers.SerializerMethodField('_end')
    all_day = serializers.SerializerMethodField('_all_day')
    is_birthday = serializers.SerializerMethodField('_is_birthday')
    url = serializers.SerializerMethodField('_url')
    title = serializers.SerializerMethodField('_title')
    description = serializers.SerializerMethodField('_description')
    background_color = serializers.SerializerMethodField('_background_color')
    text_color = serializers.SerializerMethodField('_text_color')
    target_blank = serializers.SerializerMethodField('_target_blank')

    def _start(self, instance):
        return timezone.localtime(instance.start)

    def _end(self, instance):
        return timezone.localtime(instance.end)

    def _all_day(self, instance):
        return False

    def _is_birthday(self, instance):
        return False

    def _url(self, instance):
        raise NotImplementedError

    def _title(self, instance):
        return instance.title

    def _description(self, instance):
        return instance.description

    def _background_color(self, instance):
        pass

    def _text_color(self, instance):
        pass

    def _target_blank(self, instance):
        return False


class EventSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse('events:event', kwargs={'event_id': instance.id})
