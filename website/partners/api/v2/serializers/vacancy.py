from partners.models import Vacancy
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


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
        )
