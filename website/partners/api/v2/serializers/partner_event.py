from rest_framework import serializers

from partners.models import PartnerEvent
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer


class PartnerEventSerializer(serializers.ModelSerializer):
    """Partner events serializer."""

    class Meta:
        """Meta class for partner events serializer."""

        model = PartnerEvent
        fields = ("pk", "title", "description", "start", "end", "location", "url")

    description = CleanedHTMLSerializer()
