from facedetection.models import ReferenceFace
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from thaliawebsite.api.v2.serializers.thumbnail import ThumbnailSerializer


class ReferenceFaceSerializer(CleanedModelSerializer):
    class Meta:
        model = ReferenceFace
        fields = (
            "pk",
            "status",
            "created_at",
            "file",
        )

        read_only_fields = ("status",)

    file = ThumbnailSerializer()
