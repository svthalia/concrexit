from rest_framework import serializers

from photos.models import Photo
from thaliawebsite.api.v2.serializers import ThumbnailSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class PhotoSerializer(CleanedModelSerializer):
    """API serializer for photos."""

    class Meta:
        """Meta class for the serializer."""

        model = Photo
        fields = ("pk", "file")

    file = ThumbnailSerializer(
        size_medium="photo_medium",
        size_large="photo_large",
    )


class PhotoListSerializer(PhotoSerializer):
    class Meta:
        """Meta class for the serializer."""

        model = Photo
        fields = (
            "pk",
            "file",
            "num_likes",
            "liked",
        )

    liked = serializers.SerializerMethodField("_liked")

    def _liked(self, instance):
        return self.context["request"].member and instance.member_likes > 0
