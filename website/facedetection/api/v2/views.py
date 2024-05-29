from django.conf import settings
from django.utils import timezone

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import DestroyAPIView, ListAPIView, ListCreateAPIView
from rest_framework.schemas.openapi import AutoSchema

from facedetection.services import get_user_photos
from photos.api.v2.serializers.photo import PhotoListSerializer
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from utils.media.services import fetch_thumbnails

from .serializers import ReferenceFaceSerializer


class YourPhotosView(ListAPIView):
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["photos:read", "facedetection:read"]

    schema = AutoSchema(operation_id_base="FacedetectionMatches")

    def get(self, request, *args, **kwargs):
        if not request.member or request.member.current_membership is None:
            raise PermissionDenied(
                detail="You need to be a member in order to view your facedetection photos."
            )
        return self.list(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        if len(args) > 0:
            photos = args[0]
            fetch_thumbnails([photo.file for photo in photos])
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return get_user_photos(self.request.member)


class ReferenceFaceListView(ListCreateAPIView):
    serializer_class = ReferenceFaceSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["facedetection:read"],
        "POST": ["facedetection:write"],
    }

    def get_serializer(self, *args, **kwargs):
        if len(args) > 0:
            reference_faces = args[0]
            fetch_thumbnails([reference.file for reference in reference_faces])
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if request.member.current_membership is None:
            raise PermissionDenied(
                detail="You need to be a member to use this feature."
            )
        if (
            request.member.reference_faces.filter(
                marked_for_deletion_at__isnull=True,
            ).count()
            >= settings.FACEDETECTION_MAX_NUM_REFERENCE_FACES
        ):
            raise PermissionDenied(
                detail="You have reached the maximum number of reference faces."
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.member)

    def get_queryset(self):
        return self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).all()


class ReferenceFaceDeleteView(DestroyAPIView):
    serializer_class = ReferenceFaceSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["facedetection:write"]

    def get_queryset(self):
        return self.request.member.reference_faces.filter(
            marked_for_deletion_at__isnull=True
        ).all()

    def perform_destroy(self, instance):
        instance.marked_for_deletion_at = timezone.now()
        instance.save()
