from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

from partners.api.v2 import filters
from partners.api.v2.serializers import VacancyCategorySerializer
from partners.api.v2.serializers.partner import PartnerSerializer
from partners.api.v2.serializers.vacancy import VacancySerializer
from partners.models import Partner, Vacancy, VacancyCategory
from utils.media.services import fetch_thumbnails_db


class PartnerListView(ListAPIView):
    """Returns an overview of all partners."""

    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
    )

    def get_serializer(self, *args, **kwargs):
        if len(args) > 0:
            partners = args[0]
            fetch_thumbnails_db([partner.logo for partner in partners])
        return super().get_serializer(*args, **kwargs)

    ordering_fields = ("name", "pk")
    search_fields = ("name",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]


class PartnerDetailView(RetrieveAPIView):
    """Returns a single partner."""

    serializer_class = PartnerSerializer
    queryset = Partner.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]


class VacancyListView(ListAPIView):
    """Returns an overview of all vacancies."""

    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all().prefetch_related("categories")
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.VacancyPartnerFilter,
        filters.VacancyCategoryFilter,
    )
    ordering_fields = ("title", "pk")
    search_fields = (
        "title",
        "company_name",
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]


class VacancyDetailView(RetrieveAPIView):
    """Returns a single vacancy."""

    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all()
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]


class VacancyCategoryListView(ListAPIView):
    """Returns an overview of all vacancy categories."""

    serializer_class = VacancyCategorySerializer
    queryset = VacancyCategory.objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
    )
    ordering_fields = ("name", "slug")
    search_fields = ("name",)
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["partners:read"]
