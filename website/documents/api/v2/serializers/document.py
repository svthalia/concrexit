from rest_framework.fields import SerializerMethodField

from documents.models import Document
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from utils.media.services import get_media_url


class DocumentSerializer(CleanedModelSerializer):
    class Meta:
        model = Document
        fields = ("pk", "name", "url", "category", "members_only")

    url = SerializerMethodField("_url")

    def _url(self, instance):
        if instance.members_only and (
            not self.request.user.is_authenticated
            or not self.request.member.has_active_membership()
        ):
            return self.request.build_absolute_uri(instance.get_absolute_url())
        else:
            return get_media_url(instance.file, absolute_url=True)
