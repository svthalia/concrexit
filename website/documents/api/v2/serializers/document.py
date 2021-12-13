from rest_framework.fields import SerializerMethodField
from rest_framework.reverse import reverse

from documents.models import Document
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class DocumentSerializer(CleanedModelSerializer):
    class Meta:
        model = Document
        fields = ("pk", "name", "url", "category", "members_only")

    url = SerializerMethodField("_url")

    def _url(self, instance):
        return self.context["request"].build_absolute_uri(
            reverse("documents:document", kwargs={"pk": instance.pk})
        )
