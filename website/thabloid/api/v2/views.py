from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

from thabloid.api.v2.serializers import ThabloidSerializer
from thabloid.models.thabloid import Thabloid


class ThabloidListView(ListAPIView):
    """Returns a list of all Thabloids."""

    serializer_class = ThabloidSerializer

    queryset = Thabloid.objects.all()

    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["thabloid:read"]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("year", "issue")


class ThabloidDetailView(RetrieveAPIView):
    """Returns details about a specific Thabloid."""

    serializer_class = ThabloidSerializer

    queryset = Thabloid.objects.all()

    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["thabloid:read"]
