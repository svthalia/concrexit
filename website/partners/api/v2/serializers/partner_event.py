from partners.models import PartnerEvent
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class PartnerEventSerializer(CleanedModelSerializer):
    """Partner events serializer."""

    class Meta:
        """Meta class for partner events serializer."""

        model = PartnerEvent
        fields = ("pk", "title", "description", "start", "end", "location", "url")

    description = CleanedHTMLSerializer()
