"""DRF serializers defined by the announcements package."""
from django.conf import settings

from rest_framework import serializers

from announcements.models import Slide
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer
from utils.media.services import get_thumbnail_url


class SlideSerializer(CleanedModelSerializer):
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

    content = serializers.SerializerMethodField("_file")

    def _file(self, obj):
        return self.context["request"].build_absolute_uri(
            get_thumbnail_url(obj.content, settings.THUMBNAIL_SIZES["slide"])
        )
