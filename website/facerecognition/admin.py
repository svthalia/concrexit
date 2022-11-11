from django.contrib import admin

from facerecognition.models import ReferenceFace, FaceRecognitionPhoto, FaceEncoding


class EncodingInline(admin.TabularInline):
    model = FaceEncoding
    extra = 0
    fields = ("encoding",)
    readonly_fields = ("encoding",)


@admin.register(FaceRecognitionPhoto)
class FaceRecognitionPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "photo",
        "num_faces",
    )
    search_fields = ("photo__title",)
    readonly_fields = ("num_faces",)

    inlines = [
        EncodingInline,
    ]


@admin.register(ReferenceFace)
class ReferenceFaceAdmin(admin.ModelAdmin):
    list_display = ("member",)
    readonly_fields = (
        "encoding",
        "matches",
        "marked_for_deletion_at",
    )
    autocomplete_fields = ("member",)
