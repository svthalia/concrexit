from rest_framework import serializers

from photos import services
from photos.api.v2.serializers.photo import PhotoSerializer, PhotoListSerializer
from photos.models import Album
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class AlbumSerializer(CleanedModelSerializer):
    """API serializer for albums."""

    class Meta:
        """Meta class for the serializer."""

        model = Album
        fields = (
            "slug",
            "title",
            "accessible",
            "shareable",
            "cover",
            "photos",
            "event",
        )

    cover = PhotoSerializer()
    accessible = serializers.SerializerMethodField("_accessible")
    photos = PhotoListSerializer(source="photo_set", many=True)

    def _accessible(self, obj):
        return services.is_album_accessible(self.context["request"], obj)


class AlbumListSerializer(AlbumSerializer):
    class Meta:
        """Meta class for the serializer."""

        model = Album
        fields = ("slug", "title", "accessible", "shareable", "cover", "event")
