import json

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from photos import services
from photos.api.v2.serializers.album import AlbumListSerializer, AlbumSerializer
from photos.api.v2.serializers.face_recognition import (
    PhotoFaceEncodingSerializer,
    ReferenceFaceEncodingSerializer,
)
from photos.models import Album, Photo, Like, FaceEncoding, ReferenceFace


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


# class PersonOnPhotoView(APIView):
#     permission_classes = [IsAuthenticatedOrTokenHasScope]
#     required_scopes = ["photos:read"]
#
#     def get(self, request, **kwargs):
#         photo_id = kwargs.get("pk")
#         try:
#             photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
#         except Photo.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         return Response(
#             {
#                 "on_photo": photo.persons.filter(member=request.member).exists(),
#             },
#             status=status.HTTP_200_OK,
#         )
#
#     def post(self, request, **kwargs):
#         photo_id = kwargs.get("pk")
#         try:
#             photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
#         except Photo.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         _, created = PersonOnPhoto.objects.get_or_create(photo=photo, member=request.member, defaults={"self_indicated": True})
#
#         if created:
#             return Response(
#                 {
#                     "on_photo": photo.persons.filter(
#                         member=request.member).exists(),
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         return Response(
#             {
#                 "on_photo": photo.persons.filter(member=request.member).exists(),
#             },
#             status=status.HTTP_200_OK,
#         )
#
#     def delete(self, request, **kwargs):
#         photo_id = kwargs.get("pk")
#         try:
#             photo = Photo.objects.filter(album__hidden=False).get(pk=photo_id)
#         except Photo.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         try:
#             person_on_photo = PersonOnPhoto.objects.filter(photo__album__hidden=False).get(
#                 member=request.member, photo__pk=photo_id
#             )
#         except PersonOnPhoto.DoesNotExist:
#             return Response(
#                 {
#                     "on_photo": photo.persons.filter(
#                         member=request.member).exists(),
#                 },
#                 status=status.HTTP_204_NO_CONTENT,
#             )
#
#         person_on_photo.delete()
#
#         return Response(
#             {
#                 "on_photo": photo.persons.filter(member=request.member).exists(),
#             },
#             status=status.HTTP_202_ACCEPTED,
#         )
#


class UnprocessedFaceRecognitionView(GenericAPIView):
    serializer_class = PhotoFaceEncodingSerializer
    page_size = 10

    def unprocessed_photos_queryset(self):
        return Photo.objects.filter(
            album__hidden=False,
            face_recognition_processed=False,
        )

    def unprocessed_reference_faces_queryset(self):
        return ReferenceFace.objects.filter(
            encoding__isnull=True,
        )

    def get(self, request, **kwargs):
        reference_faces = self.unprocessed_reference_faces_queryset()
        data = []

        reference_faces = reference_faces[: self.page_size]
        data += ReferenceFaceEncodingSerializer(
            reference_faces,
            context={"request": self.request},
            many=True,
        ).data
        if not reference_faces.count() >= self.page_size:
            photos = self.unprocessed_photos_queryset()[
                : self.page_size - reference_faces.count()
            ]
            data += PhotoFaceEncodingSerializer(
                photos,
                context={"request": self.request},
                many=True,
            ).data

        return Response(
            {
                "results": data,
            },
            status=status.HTTP_200_OK,
        )


class FaceEncodingPostView(APIView):
    def post(self, request, **kwargs):
        obj_type = kwargs.get("type")
        pk = kwargs.get("pk")

        if obj_type == "photo":
            obj_class = Photo
        elif obj_type == "reference_face":
            obj_class = ReferenceFace
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        obj = obj_class.objects.get(pk=pk)

        encoding_data = json.loads(request.data.get("encodings"))
        if encoding_data is None:  # TODO more sanity checks
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if obj_type == "photo":
            obj.face_encodings.all().delete()
            for encoding in encoding_data:
                FaceEncoding.objects.create(photo=obj, encoding=encoding)
            obj.face_recognition_processed = True
        elif obj_type == "reference_face":
            obj.encoding = FaceEncoding.objects.create(encoding=encoding_data[0])

        obj.save()
        return Response(status=status.HTTP_200_OK)
