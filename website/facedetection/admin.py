from typing import Any, List, Optional, Tuple, Union

from django.contrib import admin
from django.db.models.query import Prefetch, QuerySet
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    FaceDetectionPhoto,
    PhotoFaceEncoding,
    ReferenceFace,
    ReferenceFaceEncoding,
)


class ReferenceFaceEncodingInline(admin.TabularInline):
    model = ReferenceFaceEncoding
    readonly_fields = ["num_matches"]
    fields = ["num_matches"]
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False  # Encodings should not be created manually.

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).only("reference")


@admin.register(ReferenceFace)
class ReferenceFaceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "status",
        "created_at",
        "marked_for_deletion_at",
    ]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
    ]

    list_filter = ["status", "marked_for_deletion_at"]
    inlines = [ReferenceFaceEncodingInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ["created_at", "submitted_at", "status"]
        return ["file", "user", "created_at", "submitted_at", "status"]


class PhotoFaceEncodingInline(admin.TabularInline):
    model = PhotoFaceEncoding
    readonly_fields = ["view_matches"]
    fields = ["view_matches"]
    can_delete = False
    extra = 0

    @admin.display(description="Matches")
    def view_matches(self, obj):
        reference_faces = [match.reference for match in obj.matches.all()]
        if not reference_faces:
            return "-"

        links = [
            format_html(
                '<a href="{url}">{text}</a>',
                url=reverse(
                    "admin:facedetection_referenceface_change",
                    kwargs={"object_id": rf.pk},
                ),
                text=str(rf),
            )
            for rf in reference_faces
        ]
        return mark_safe(", ".join(links))

    def has_add_permission(self, request, obj=None):
        return False  # Encodings should not be created manually.

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .only("photo")  # Don't select the 128 encoding fields.
            .prefetch_related(
                "photo__photo__album",
                Prefetch(
                    "matches",
                    queryset=ReferenceFaceEncoding.objects.select_related(
                        "reference", "reference__user"
                    ).only("reference"),
                ),
            )
        )


@admin.register(FaceDetectionPhoto)
class FaceDetectionPhotoAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "status",
        "submitted_at",
        "num_faces",
    ]

    readonly_fields = [
        "photo",
        "submitted_at",
        "status",
    ]

    search_fields = [
        "photo__album__title",
        "photo__album__date",
        "photo__file",
    ]

    list_filter = ["status", "submitted_at"]
    inlines = [PhotoFaceEncodingInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("photo")
            .prefetch_related("photo__album")
            .select_properties("num_faces")
        )

    def has_add_permission(self, request):
        return False
