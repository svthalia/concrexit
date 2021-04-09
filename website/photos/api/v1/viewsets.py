from rest_framework import permissions, filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from photos import services
from photos.api.v1 import serializers
from photos.models import Album, Photo


class AlbumsViewSet(ModelViewSet):
    """ViewSet class for an Album object."""

    permission_classes = (permissions.IsAuthenticated,)
    queryset = Album.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title", "date", "slug")

    def get_queryset(self):
        """Return albums that are annotated to be accessible by the request user."""
        return services.get_annotated_accessible_albums(
            self.request, Album.objects.all()
        )

    def create(self, request, *args, **kwargs):
        """Create album if the request user is allowed to."""
        if self.request.user.has_perm("photos.create_album"):
            return super().create(request, *args, **kwargs)
        raise PermissionDenied

    def update(self, request, *args, **kwargs):
        """Create album if the request user is allowed to."""
        if self.request.user.has_perm("photos.change_album"):
            return super().update(request, *args, **kwargs)
        raise PermissionDenied

    def get_serializer_class(self):
        """Return AlbumListSerializer if the current action is list else return AlbumSerializer."""
        if self.action == "list":
            return serializers.AlbumListSerializer
        return serializers.AlbumSerializer


class PhotosViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    """ViewSet class for a Photo object."""

    queryset = Photo.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PhotoCreateSerializer

    def create(self, request, *args, **kwargs):
        """Create photo if the request user is allowed to."""
        if self.request.user.has_perm("photos.create_photo"):
            return super().create(request, *args, **kwargs)
        raise PermissionDenied

    def update(self, request, *args, **kwargs):
        """Update photo if the request user is allowed to."""
        if self.request.user.has_perm("photos.change_photo"):
            return super().update(request, *args, **kwargs)
        raise PermissionDenied
