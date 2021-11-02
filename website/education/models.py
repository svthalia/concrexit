"""The models defined by the education package."""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members.models import Member
from utils.snippets import datetime_to_lectureyear


class Category(models.Model):
    """Describes a course category."""

    name = models.CharField(max_length=64,)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("education:category", args=[str(self.pk)])

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class Course(models.Model):
    """Describes a course."""

    name = models.CharField(max_length=255)

    categories = models.ManyToManyField(
        Category, verbose_name=_("categories"), blank=True
    )

    old_courses = models.ManyToManyField(
        "self", symmetrical=False, verbose_name=_("old courses"), blank=True
    )

    course_code = models.CharField(max_length=16)

    ec = models.IntegerField(verbose_name=_("EC"))

    since = models.IntegerField()
    until = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.course_code})"

    def get_absolute_url(self):
        return reverse("education:course", args=[str(self.pk)])

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("course")
        verbose_name_plural = _("courses")


class Exam(models.Model):
    """Describes an exam."""

    EXAM_TYPES = (
        ("document", _("Document")),
        ("exam", _("Exam")),
        ("partial", _("Partial Exam")),
        ("resit", _("Resit")),
        ("practice", _("Practice Exam")),
        ("exam_answers", _("Exam Answers")),
        ("partial_answers", _("Partial Exam Answers")),
        ("resit_answers", _("Resit Answers")),
        ("practice_answers", _("Practice Exam Answers")),
    )

    type = models.CharField(
        max_length=40, choices=EXAM_TYPES, verbose_name=_("exam type"),
    )

    name = models.CharField(max_length=255, verbose_name=_("exam name"), blank=True)

    uploader = models.ForeignKey(
        Member, verbose_name=_("uploader"), on_delete=models.SET_NULL, null=True,
    )

    uploader_date = models.DateField(default=timezone.now,)

    accepted = models.BooleanField(verbose_name=_("accepted"), default=False,)

    exam_date = models.DateField(verbose_name=_("exam date"),)

    file = models.FileField(
        upload_to="education/files/exams/",
        help_text=_(
            "Use the 'View on site' button to download the file for inspection."
        ),
    )

    course = models.ForeignKey(
        Course, verbose_name=_("course"), on_delete=models.CASCADE,
    )

    language = models.CharField(
        max_length=2,
        choices=[("en", "English"), ("nl", "Dutch")],
        blank=False,
        null=True,
    )

    download_count = models.IntegerField(
        verbose_name=_("amount of downloads"), default=0, blank=False,
    )

    def __str__(self):
        return f"{self.name.capitalize()} {self.type.capitalize()} ({self.course.name}, {self.course.course_code}, {self.exam_date})"

    def get_absolute_url(self):
        return reverse("education:exam", args=[str(self.pk)])

    @property
    def year(self):
        return datetime_to_lectureyear(self.exam_date)

    class Meta:
        verbose_name = _("exam")
        verbose_name_plural = _("exams")


class Summary(models.Model):
    """Describes a summary."""

    name = models.CharField(max_length=255, verbose_name=_("summary name"),)

    uploader = models.ForeignKey(
        Member, verbose_name=_("uploader"), on_delete=models.SET_NULL, null=True,
    )

    uploader_date = models.DateField(default=timezone.now,)

    year = models.IntegerField()

    author = models.CharField(max_length=64, verbose_name=_("author"),)

    course = models.ForeignKey(
        Course, verbose_name=_("course"), on_delete=models.CASCADE,
    )

    accepted = models.BooleanField(verbose_name=_("accepted"), default=False,)

    file = models.FileField(
        upload_to="education/files/summary/",
        help_text=_(
            "Use the 'View on site' button to download the file for inspection."
        ),
    )

    language = models.CharField(
        max_length=2,
        choices=[("en", "English"), ("nl", "Dutch")],
        blank=False,
        null=True,
    )

    download_count = models.IntegerField(
        verbose_name=_("amount of downloads"), default=0, blank=False,
    )

    def __str__(self):
        return (
            f"{self.name} ({self.course.name}, {self.course.course_code}, {self.year})"
        )

    def get_absolute_url(self):
        return reverse("education:summary", args=[str(self.pk)])

    class Meta:
        verbose_name = _("summary")
        verbose_name_plural = _("summaries")
