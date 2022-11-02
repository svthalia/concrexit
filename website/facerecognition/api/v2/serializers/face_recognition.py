from rest_framework import serializers

from facerecognition.models import ReferenceFace
from photos.models import Photo
from thaliawebsite.api.v2.serializers import ThumbnailSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class ReferenceFaceEncodingSerializer(CleanedModelSerializer):
    class Meta:
        model = ReferenceFace
        fields = ("pk", "type", "file")

    file = ThumbnailSerializer(
        size_medium="1200x900",
        size_large="1920x1920",
        fit_medium=False,
        fit_large=False,
    )

    type = serializers.ReadOnlyField(default="reference_face")


class PhotoFaceEncodingSerializer(CleanedModelSerializer):
    class Meta:
        model = Photo
        fields = ("pk", "type", "file")

    file = ThumbnailSerializer(
        size_medium="1200x900",
        size_large="1920x1920",
        fit_medium=False,
        fit_large=False,
    )

    type = serializers.ReadOnlyField(default="photo")
