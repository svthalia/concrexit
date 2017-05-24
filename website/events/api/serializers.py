from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import serializers

from events.models import Event


class CalenderJSSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'start', 'end', 'all_day', 'is_birthday',
            'url', 'title', 'description',
            'backgroundColor', 'textColor', 'blank',
            'registered'
        )

    start = serializers.SerializerMethodField('_start')
    end = serializers.SerializerMethodField('_end')
    all_day = serializers.SerializerMethodField('_all_day')
    is_birthday = serializers.SerializerMethodField('_is_birthday')
    url = serializers.SerializerMethodField('_url')
    title = serializers.SerializerMethodField('_title')
    description = serializers.SerializerMethodField('_description')
    backgroundColor = serializers.SerializerMethodField('_background_color')
    textColor = serializers.SerializerMethodField('_text_color')
    blank = serializers.SerializerMethodField('_target_blank')
    registered = serializers.SerializerMethodField('_registered')

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
        return strip_tags(instance.description)

    def _background_color(self, instance):
        pass

    def _text_color(self, instance):
        pass

    def _target_blank(self, instance):
        return False

    def _registered(self, instance):
        return None


class EventCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse('events:event', kwargs={'event_id': instance.id})

    def _registered(self, instance):
        try:
            return instance.is_member_registered(self.context['user'].member)
        except AttributeError:
            return None


class UnpublishedEventSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _background_color(self, instance):
        return "#888888"

    def _text_color(self, instance):
        return "white"

    def _url(self, instance):
        return reverse('events:admin-details', kwargs={
            'event_id': instance.id})


class EventRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('title', 'description', 'start', 'end', 'organiser',
                  'location', 'price', 'fine')

    description = serializers.SerializerMethodField('_description')

    def _description(self, instance):
        return strip_tags(instance.description)


class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('title', 'description', 'start',
                  'location', 'price', 'id')

    description = serializers.SerializerMethodField('_description')

    def _description(self, instance):
        return strip_tags(instance.description)
