from html import unescape

from django.utils.html import strip_tags

from rest_framework import serializers

from events.models.external_event import ExternalEvent


class ExternalEventSerializer(serializers.ModelSerializer):
    """External events serializer."""

    class Meta:
        """Meta class for partner events serializer."""

        model = ExternalEvent
        fields = ("pk", "title", "description", "start", "end", "location", "url")

    description = serializers.SerializerMethodField("_description")

    def _description(self, instance):
        """Return description of partner event."""
        return unescape(strip_tags(instance.description))
