from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from partners.models import PartnerEvent, Partner


class PartnerEventCalendarJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = PartnerEvent

    def _title(self, instance):
        return "{} ({})".format(instance.title, instance.partner.name)

    def _background_color(self, instance):
        return '#E62272'

    def _text_color(self, instance):
        return 'white'

    def _url(self, instance):
        return instance.url

    def _target_blank(self, instance):
        return True


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ('pk', 'name', 'link', 'company_profile', 'address',
                  'zip_code', 'city', 'logo')


class PartnerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerEvent
        fields = ('pk', 'title', 'description', 'start', 'end', 'location',
                  'url')

    description = serializers.SerializerMethodField('_description')

    def _description(self, instance):
        return unescape(strip_tags(instance.description))
