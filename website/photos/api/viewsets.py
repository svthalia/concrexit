from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, \
    UpdateModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from photos import services
from photos.api import serializers
from photos.models import Album, Photo


class AlbumsViewSet(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Album.objects.all()

    def get_queryset(self):
        return services.get_annotated_accessible_albums(self.request,
                                                        Album.objects.all())

    def create(self, request, *args, **kwargs):
        if self.request.user.has_perm('photos.create_album'):
            return super().create(request, *args, **kwargs)
        raise PermissionDenied

    def update(self, request, *args, **kwargs):
        if self.request.user.has_perm('photos.change_album'):
            return super().update(request, *args, **kwargs)
        raise PermissionDenied

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.AlbumListSerializer
        return serializers.AlbumSerializer


class PhotosViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    queryset = Photo.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PhotoCreateSerializer

    def create(self, request, *args, **kwargs):
        if self.request.user.has_perm('photos.create_photo'):
            return super().create(request, *args, **kwargs)
        raise PermissionDenied

    def update(self, request, *args, **kwargs):
        if self.request.user.has_perm('photos.change_photo'):
            return super().update(request, *args, **kwargs)
        raise PermissionDenied
