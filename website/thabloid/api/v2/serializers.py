from rest_framework import serializers

from thabloid.models.thabloid import Thabloid
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from utils.media.services import get_media_url


class ThabloidSerializer(CleanedModelSerializer):
    """API Serializer for thabloids."""

    file = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the serializer."""

        model = Thabloid
        fields = ("pk", "year", "issue", "cover", "file")

    def get_cover(self, instance):
        return get_media_url(instance.cover, absolute_url=True)

    def get_file(self, instance):
        return get_media_url(instance.file, absolute_url=True)
