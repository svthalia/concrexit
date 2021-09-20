from html import unescape

from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import serializers


class CalenderJSSerializer(serializers.ModelSerializer):
    """Serializer using the right format for CalendarJS."""

    class Meta:
        fields = (
            "start",
            "end",
            "allDay",
            "isBirthday",
            "url",
            "title",
            "description",
            "classNames",
            "blank",
        )

    start = serializers.SerializerMethodField("_start")
    end = serializers.SerializerMethodField("_end")
    allDay = serializers.SerializerMethodField("_all_day")
    isBirthday = serializers.SerializerMethodField("_is_birthday")
    url = serializers.SerializerMethodField("_url")
    title = serializers.SerializerMethodField("_title")
    description = serializers.SerializerMethodField("_description")
    classNames = serializers.SerializerMethodField("_class_names")
    blank = serializers.SerializerMethodField("_target_blank")

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
        return unescape(strip_tags(instance.description))

    def _class_names(self, instance):
        pass

    def _target_blank(self, instance):
        return False
