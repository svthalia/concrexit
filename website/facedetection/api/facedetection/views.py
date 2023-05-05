import json

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import (
    BaseFaceEncodingSource,
    FaceDetectionPhoto,
    PhotoFaceEncoding,
    ReferenceFace,
    ReferenceFaceEncoding,
)


class FaceEncodingPostView(APIView):
    def post(self, request, **kwargs):
        """Submit encodings for a face encoding source.

        Expects a json body as follows:

        {
            "type": "reference" | "photo",
            "token": str,       # The base64 token for authentication.
            "pk": int,          # The pk of the ReferenceFace or FaceDetectionPhoto.
            "encodings": [      # A list of 0 or more encodings.
                [ <128 floats> ],
                ...
            ],
        }
        """

        pk = kwargs["pk"]
        obj_type = kwargs["type"]

        if obj_type == "reference":
            obj = get_object_or_404(ReferenceFace, pk=pk)
        elif obj_type == "photo":
            obj = get_object_or_404(FaceDetectionPhoto, pk=pk)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            encodings = request.data["encodings"]
            token = request.data["token"]
        except (json.JSONDecodeError, KeyError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(token, str) or not isinstance(encodings, list):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        for encoding in encodings:
            if (
                not isinstance(encoding, list)
                or len(encoding) != 128
                or not all(isinstance(value, float) for value in encoding)
            ):
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if obj.token != token:
            raise PermissionDenied(detail="Invalid token.")
        elif obj.status != BaseFaceEncodingSource.Status.PROCESSING:
            raise ValidationError(detail="This object is not processing.")

        if isinstance(obj, ReferenceFace):
            if len(encodings) == 1:
                reference_encoding = ReferenceFaceEncoding(reference=obj)
                reference_encoding.encoding = encodings[0]
                reference_encoding.save()
                obj.status = BaseFaceEncodingSource.Status.DONE
                obj.save()
            else:  # ReferenceFace needs exactly one encoding.
                obj.status = BaseFaceEncodingSource.Status.REJECTED
                obj.save()
        elif isinstance(obj, FaceDetectionPhoto):
            for encoding in encodings:
                photo_face_encoding = PhotoFaceEncoding(photo=obj)
                photo_face_encoding.encoding = encoding
                photo_face_encoding.save()
            obj.status = BaseFaceEncodingSource.Status.DONE
            obj.save()

        return Response(status=status.HTTP_200_OK)
