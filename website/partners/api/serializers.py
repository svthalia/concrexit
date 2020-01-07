from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from events.api.serializers import CalenderJSSerializer
from partners.models import PartnerEvent, Partner


class PartnerEventCalendarJSSerializer(CalenderJSSerializer):
    """Partner event calender serializer."""

    class Meta(CalenderJSSerializer.Meta):
        """Meta class for partner event calendar serializer."""

        model = PartnerEvent

    def _title(self, instance):
        if instance.partner:
            return "{} ({})".format(instance.title, instance.partner.name)
        return "{} ({})".format(instance.title, instance.other_partner)

    def _background_color(self, instance):
        """Return the color of the background."""
        return "black"

    def _text_color(self, instance):
        """Return the color of the text."""
        return "#E62272"

    def _url(self, instance):
        """Return the url of the partner event."""
        return instance.url

    def _target_blank(self, instance):
        """Return whether the anchor tag should have 'target="_blank"'."""
        return True


class PartnerSerializer(serializers.ModelSerializer):
    """Partner serializer."""

    class Meta:
        """Meta class for partner serializer."""

        model = Partner
        fields = (
            "pk",
            "name",
            "link",
            "company_profile",
            "address",
            "zip_code",
            "city",
            "logo",
        )


class PartnerEventSerializer(serializers.ModelSerializer):
    """Partner events serializer."""

    class Meta:
        """Meta class for partner events serializer."""

        model = PartnerEvent
        fields = ("pk", "title", "description", "start", "end", "location", "url")

    description = serializers.SerializerMethodField("_description")

    def _description(self, instance):
        """Return description of partner event."""
        return unescape(strip_tags(instance.description))
