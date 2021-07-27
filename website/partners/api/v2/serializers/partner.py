from rest_framework import serializers

from partners.models import Partner
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer, ThumbnailSerializer


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

    company_profile = CleanedHTMLSerializer()
    logo = ThumbnailSerializer()
