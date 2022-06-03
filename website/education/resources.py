from import_export import resources
from import_export.fields import Field

from .models import Exam


class ExamResource(resources.ModelResource):
    id = Field(attribute="id", column_name="id")
    type = Field(attribute="type", column_name="Type")
    name = Field(attribute="name", column_name="Name")
    uploader = Field(attribute="uploader", column_name="Uploader")
    uploader_date = Field(attribute="uploader_date", column_name="Uploader date")
    accepted = Field(attribute="accepted", column_name="Accepted")
    exam_date = Field(attribute="exam_date", column_name="Exam date")
    file = Field(attribute="file", column_name="File")
    course = Field(attribute="course", column_name="Course")
    language = Field(attribute="language", column_name="Language")
    download_count = Field(attribute="download_count", column_name="Download count")

    class Meta:
        model = Exam
        fields = (
            "id",
            "type",
            "name",
            "uploader",
            "uploader_date",
            "accepted",
            "exam_date",
            "file",
            "course",
            "language",
            "download_count",
        )
        export_order = (
            "id",
            "type",
            "name",
            "uploader",
            "uploader_date",
            "accepted",
            "exam_date",
            "file",
            "course",
            "language",
            "download_count",
        )
