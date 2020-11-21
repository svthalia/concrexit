from django.conf import settings
from rest_framework import serializers

from announcements.models import Slide
from thaliawebsite.api.v2.serializers.thumbnail import ThumbnailSerializer


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

    content = ThumbnailSerializer(
        size_large=settings.THUMBNAIL_SIZES["slide"],
        size_medium=settings.THUMBNAIL_SIZES["slide_medium"],
        size_small=settings.THUMBNAIL_SIZES["slide_small"],
    )
