from rest_framework import serializers

from partners.models import Vacancy
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from thaliawebsite.api.v2.serializers.thumbnail import ThumbnailSerializer

from .vacancy_category import VacancyCategorySerializer


class VacancySerializer(CleanedModelSerializer):
    """Vacancy serializer."""

    class Meta:
        """Meta class for vacancy serializer."""

        model = Vacancy
        fields = (
            "pk",
            "title",
            "description",
            "location",
            "keywords",
            "link",
            "partner",
            "company_name",
            "company_logo",
            "categories",
        )

    company_name = serializers.CharField(source="get_company_name", read_only=True)
    company_logo = serializers.SerializerMethodField("_company_logo")

    def _company_logo(self, instance):
        return ThumbnailSerializer().to_representation(instance.get_company_logo())

    categories = VacancyCategorySerializer(many=True)
