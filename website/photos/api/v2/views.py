from django.db.models import Count, Prefetch, Q

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from photos import services
from photos.api.v2.serializers.album import (
    AlbumListSerializer,
    AlbumSerializer,
    PhotoListSerializer,
)
from photos.models import Album, Like, Photo
from utils.media.services import fetch_thumbnails_db


class AlbumListView(ListAPIView):
    """Returns an overview of all albums."""

    serializer_class = AlbumListSerializer

    def get_queryset(self):
        albums = Album.objects.filter(hidden=False)
        fetch_thumbnails_db([album.cover.file for album in albums if album.cover])
        return albums

    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["photos:read"]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title", "date", "slug")


class AlbumDetailView(RetrieveAPIView):
    """Returns the details of an album."""

    serializer_class = AlbumSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["photos:read"]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        if not services.is_album_accessible(request, self.get_object()):
            raise PermissionDenied
        return super().retrieve(request, *args, **kwargs)

    def get_object(self):
        object = super().get_object()
        fetch_thumbnails_db([photo.file for photo in object.photo_set.all()])
        return object

    def get_queryset(self):
        photos = Photo.objects.select_properties("num_likes")
        if self.request.member:
            photos = photos.annotate(
                member_likes=Count("likes", filter=Q(likes__member=self.request.member))
            )

        # Fix select_properties dropping the default ordering.
        photos = photos.order_by("pk")

        return Album.objects.filter(hidden=False).prefetch_related(
            Prefetch("photo_set", queryset=photos)
        )


class LikedPhotosListView(ListAPIView):
    """Returns the details the liked album."""

    serializer_class = PhotoListSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["photos:read"]

    def get(self, request, *args, **kwargs):
        if not self.request.member:
            return Response(
                data={
                    "detail": "You need to be a member in order to view your liked photos."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return self.list(request, *args, **kwargs)

    def get_serializer(self, photos, *args, **kwargs):
        fetch_thumbnails_db([photo.file for photo in photos])
        return super().get_serializer(photos, *args, **kwargs)

    def get_queryset(self):
        return (
            Photo.objects.filter(likes__member=self.request.member, album__hidden=False)
            .annotate(
                member_likes=Count("likes", filter=Q(likes__member=self.request.member))
            )
            .select_properties("num_likes")
        )


class PhotoLikeView(APIView):
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["photos:read"]

    def get(self, request, **kwargs):
        photo_id = kwargs.get("pk")
        try:
            photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
        except Photo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "liked": photo.likes.filter(member=request.member).exists(),
                "num_likes": photo.num_likes,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, **kwargs):
        photo_id = kwargs.get("pk")
        try:
            photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
        except Photo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        _, created = Like.objects.get_or_create(photo=photo, member=request.member)

        if created:
            return Response(
                {
                    "liked": photo.likes.filter(member=request.member).exists(),
                    "num_likes": photo.num_likes,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "liked": photo.likes.filter(member=request.member).exists(),
                "num_likes": photo.num_likes,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, **kwargs):
        photo_id = kwargs.get("pk")
        try:
            photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
        except Photo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.filter(photo__album__hidden=False).get(
                member=request.member, photo__pk=photo_id
            )
        except Like.DoesNotExist:
            return Response(
                {
                    "liked": False,
                    "num_likes": photo.num_likes,
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        like.delete()

        return Response(
            {
                "liked": False,
                "num_likes": photo.num_likes,
            },
            status=status.HTTP_202_ACCEPTED,
        )
