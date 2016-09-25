from django.utils import timezone
from django.urls import reverse
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from partners.models import PartnerEvent


class PartnerEventSerializer(CalenderJSSerializer):
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
