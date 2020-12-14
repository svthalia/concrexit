from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from partners.models import PartnerEvent, Partner


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
