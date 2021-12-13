from rest_framework import serializers

from partners.models import Partner
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer, ThumbnailSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


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

    company_profile = CleanedHTMLSerializer()
    logo = ThumbnailSerializer()
