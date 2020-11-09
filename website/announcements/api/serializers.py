"""DRF serializers defined by the announcements package."""
from rest_framework import serializers

from announcements.models import Slide


class SlideSerializer(serializers.ModelSerializer):
    """Slide serializer."""

    class Meta:
        """Meta class for the serializer."""

        model = Slide
        fields = (
            "pk",
            "title",
            "content",
            "order",
            "url",
        )
