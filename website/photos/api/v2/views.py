from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from photos import services
from photos.api.v2.serializers.album import AlbumListSerializer, AlbumSerializer
from photos.models import Album


class AlbumListView(ListAPIView):
    """Returns an overview of all albums."""

    serializer_class = AlbumListSerializer
    queryset = Album.objects.filter(hidden=False)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["photos:read"]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title_en", "date", "slug")


class AlbumDetailView(RetrieveAPIView):
    """Returns the details of an album."""

    serializer_class = AlbumSerializer
    queryset = Album.objects.filter(hidden=False)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["photos:read"]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        if not services.is_album_accessible(request, self.get_object()):
            raise PermissionDenied
        return super().retrieve(request, *args, **kwargs)
