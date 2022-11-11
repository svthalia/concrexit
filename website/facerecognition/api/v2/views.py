from facerecognition.api.v2.serializers.face_recognition import (
    PhotoFaceEncodingSerializer,
    ReferenceFaceEncodingSerializer,
)
from facerecognition.models import FaceEncoding, FaceRecognitionPhoto, ReferenceFace
from oauth2_provider.views.mixins import ClientProtectedResourceMixin
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from photos.models import Photo


class UnprocessedFaceRecognitionView(ClientProtectedResourceMixin, GenericAPIView):
    serializer_class = PhotoFaceEncodingSerializer
    page_size = 10

    @staticmethod
    def unprocessed_photos_queryset():
        return Photo.objects.filter(
            face_recognition_photo__isnull=True,
            album__hidden=False,
        )

    @staticmethod
    def unprocessed_reference_faces_queryset():
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


class FaceEncodingPostView(ClientProtectedResourceMixin, APIView):
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
        if encoding_data is None or (
            len(encoding_data) > 0 and any(len(enc) != 128 for enc in encoding_data)
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if obj_type == "photo":
            processed_photo, _ = FaceRecognitionPhoto.objects.get_or_create(photo=obj)
            processed_photo.encodings.all().delete()
            for encoding in encoding_data:
                FaceEncoding.objects.create(photo=processed_photo, encoding=encoding)

        elif obj_type == "reference_face":
            obj.encoding = FaceEncoding.objects.create(
                encoding=encoding_data[0]
            )  # We only support one encoding per reference face, so we take the first one
            obj.save()

        return Response(status=status.HTTP_200_OK)
