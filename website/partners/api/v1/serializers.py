from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from partners.models import PartnerEvent, Partner
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class PartnerSerializer(CleanedModelSerializer):
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


class PartnerEventSerializer(CleanedModelSerializer):
    """Partner events serializer."""

    class Meta:
        """Meta class for partner events serializer."""

        model = PartnerEvent
        fields = ("pk", "title", "description", "start", "end", "location", "url")

    description = serializers.SerializerMethodField("_description")

    def _description(self, instance):
        """Return description of partner event."""
        return unescape(strip_tags(instance.description))
