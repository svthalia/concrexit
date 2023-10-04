from import_export import resources
from import_export.fields import Field

from education.models import Exam, Summary


class ExamResource(resources.ModelResource):
    exam_id = Field(attribute="id", column_name="id")
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
            "exam_id",
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
        export_order = fields


class SummaryResource(resources.ModelResource):
    summary_id = Field(attribute="id", column_name="id")
    name = Field(attribute="name", column_name="Name")
    uploader = Field(attribute="uploader", column_name="Uploader")
    uploader_date = Field(attribute="uploader_date", column_name="Uploader date")
    year = Field(attribute="year", column_name="Year")
    author = Field(attribute="author", column_name="Author")
    course = Field(attribute="course", column_name="Course")
    accepted = Field(attribute="accepted", column_name="Accepted")
    file = Field(attribute="file", column_name="File")
    language = Field(attribute="language", column_name="Language")
    download_count = Field(attribute="download_count", column_name="Download count")

    class Meta:
        model = Summary
        fields = (
            "summary_id",
            "name",
            "uploader",
            "uploader_date",
            "year",
            "author",
            "course",
            "accepted",
            "file",
            "language",
            "download_count",
        )
        export_order = fields
