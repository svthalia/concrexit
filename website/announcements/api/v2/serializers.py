from announcements.models import Slide
from rest_framework import serializers
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer, ThumbnailSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class AnnouncementSerializer(serializers.Serializer):
    content = CleanedHTMLSerializer(read_only=True)
    closeable = serializers.BooleanField(read_only=True)
    icon = serializers.CharField(read_only=True)


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

    content = ThumbnailSerializer(
        size_large="slide",
        size_medium="slide_medium",
        size_small="slide_small",
    )


class FrontpageArticleSerializer(serializers.ModelSerializer):
    """FrontpageArticle serializer."""

    class Meta:
        """Meta class for the serializer."""

        model = Slide
        fields = ("pk", "title", "content")

    content = CleanedHTMLSerializer()
