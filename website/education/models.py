from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from utils.snippets import datetime_to_lectureyear
from utils.translation import ModelTranslateMeta, MultilingualField


class Category(models.Model, metaclass=ModelTranslateMeta):
    name = MultilingualField(
        models.CharField,
        max_length=64,
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('education:category', args=[str(self.pk)])

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class Course(models.Model, metaclass=ModelTranslateMeta):
    name = MultilingualField(
        models.CharField,
        max_length=255
    )

    categories = models.ManyToManyField(
        Category,
        verbose_name=_("categories"),
        blank=True
    )

    old_courses = models.ManyToManyField(
        'self',
        symmetrical=False,
        verbose_name=_("old courses"),
        blank=True
    )

    shorthand = MultilingualField(
        models.CharField,
        max_length=10
    )

    course_code = models.CharField(
        max_length=16
    )

    ec = models.IntegerField(
        verbose_name=_('EC')
    )

    since = models.IntegerField()
    until = models.IntegerField(
        blank=True
    )

    period = models.CharField(
        max_length=64,
        verbose_name=_('period'),
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.course_code)

    def get_absolute_url(self):
        return reverse('education:course', args=[str(self.pk)])

    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')


class Exam(models.Model):
    EXAM_TYPES = (
        ('document', _('Document')),
        ('exam', _('Exam')),
        ('partial', _('Partial Exam')),
        ('resit', _('Resit')),
        ('practice', _('Practice Exam')))

    type = models.CharField(
        max_length=40,
        choices=EXAM_TYPES,
        verbose_name=_('exam type'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('exam name'),
        blank=True
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('uploader'),
        on_delete=models.CASCADE,
    )

    uploader_date = models.DateField(
        default=timezone.now,
    )

    accepted = models.BooleanField(
        verbose_name=_('accepted'),
        default=False,
    )

    exam_date = models.DateField(
        verbose_name=_('exam date'),
    )

    file = models.FileField(
        upload_to="education/files/exams/"
    )

    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return "{} {} ({}, {}, {})".format(self.name.capitalize(),
                                           self.type.capitalize(),
                                           self.course.name,
                                           self.course.course_code,
                                           self.exam_date)

    def get_absolute_url(self):
        return reverse('education:exam', args=[str(self.pk)])

    @property
    def year(self):
        return datetime_to_lectureyear(self.exam_date)

    class Meta:
        verbose_name = _('exam')
        verbose_name_plural = _('exams')


class Summary(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('summary name'),
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('uploader'),
        on_delete=models.CASCADE,
    )

    uploader_date = models.DateField(
        default=timezone.now,
    )

    year = models.IntegerField()

    author = models.CharField(
        max_length=64,
        verbose_name=_("author"),
    )

    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        on_delete=models.CASCADE,
    )

    accepted = models.BooleanField(
        verbose_name=_('accepted'),
        default=False,
    )

    file = models.FileField(
        upload_to="education/files/summary/"
    )

    def __str__(self):
        return "{} ({}, {}, {})".format(self.name, self.course.name,
                                        self.course.course_code, self.year)

    def get_absolute_url(self):
        return reverse('education:suma', args=[str(self.pk)])

    class Meta:
        verbose_name = _('summary')
        verbose_name_plural = _('summaries')
