from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from photos import services
from photos.api.v2.serializers.album import AlbumListSerializer, AlbumSerializer
from photos.models import Album, Like, Photo


class AlbumListView(ListAPIView):
    """Returns an overview of all albums."""

    serializer_class = AlbumListSerializer
    queryset = Album.objects.filter(hidden=False)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["photos:read"]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title", "date", "slug")


class AlbumDetailView(RetrieveAPIView):
    """Returns the details of an album."""

    serializer_class = AlbumSerializer
    queryset = Album.objects.filter(hidden=False)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["photos:read"]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        if not services.is_album_accessible(request, self.get_object()):
            raise PermissionDenied
        return super().retrieve(request, *args, **kwargs)


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
