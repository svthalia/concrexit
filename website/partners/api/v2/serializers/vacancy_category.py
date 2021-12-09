from rest_framework import serializers

from partners.models import VacancyCategory


class VacancyCategorySerializer(serializers.ModelSerializer):
    """Vacancy category serializer."""

    class Meta:
        """Meta class for vacancy category serializer."""

        model = VacancyCategory
        fields = ("name", "slug")

