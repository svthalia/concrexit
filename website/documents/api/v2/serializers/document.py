from rest_framework.fields import SerializerMethodField
from rest_framework.reverse import reverse
from rest_framework.serializers import ModelSerializer

from documents.models import Document


class DocumentSerializer(ModelSerializer):
    class Meta:
        model = Document
        fields = ("pk", "name", "url", "category", "members_only")

    url = SerializerMethodField("_url")

    def _url(self, instance):
        return self.context["request"].build_absolute_uri(
            reverse("documents:document", kwargs={"pk": instance.pk})
        )
