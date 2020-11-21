from rest_framework import serializers

from announcements.models import FrontpageArticle
from thaliawebsite.api.v2.serializers.thumbnail import CleanedHTMLSerializer


class FrontpageArticleSerializer(serializers.ModelSerializer):
    """FrontpageArticle serializer."""

    class Meta:
        """Meta class for the serializer."""

        model = FrontpageArticle
        fields = ("pk", "title", "content")

    content = CleanedHTMLSerializer()
