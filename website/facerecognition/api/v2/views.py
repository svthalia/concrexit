from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from facerecognition.api.v2.serializers.face_recognition import (
    PhotoFaceEncodingSerializer,
    ReferenceFaceEncodingSerializer,
)
from facerecognition.models import ReferenceFace, FaceEncoding, FaceRecognitionPhoto
from photos.models import Photo


class UnprocessedFaceRecognitionView(GenericAPIView):
    serializer_class = PhotoFaceEncodingSerializer
    page_size = 10

    def unprocessed_photos_queryset(self):
        return Photo.objects.filter(
            face_recognition_photo__isnull=True,
            album__hidden=False,
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
            processed_photo, _ = FaceRecognitionPhoto.objects.get_or_create(photo=obj)
            processed_photo.encodings.all().delete()
            for encoding in encoding_data:
                FaceEncoding.objects.create(photo=processed_photo, encoding=encoding)

        elif obj_type == "reference_face":
            obj.encoding = FaceEncoding.objects.create(encoding=encoding_data[0])
            obj.save()

        return Response(status=status.HTTP_200_OK)
