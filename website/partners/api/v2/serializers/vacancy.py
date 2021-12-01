from rest_framework import serializers

from partners.models import Vacancy


class VacancySerializer(serializers.ModelSerializer):
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
