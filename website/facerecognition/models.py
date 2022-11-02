import os

from django.db import models
from django.db.models import Count, IntegerField, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from queryable_properties.properties import AnnotationProperty

from members.models import Member
from photos.models import Photo


class FaceRecognitionPhoto(models.Model):

    photo = models.OneToOneField(
        Photo,
        verbose_name=_("Face recognition photo"),
        null=False,
        blank=False,
        related_name="face_recognition_photo",
        on_delete=models.CASCADE,
    )

    num_faces = AnnotationProperty(
        Coalesce(Count("encodings"), Value(0), output__field=IntegerField())
    )

    def __str__(self):
        return str(self.photo)

    class Meta:
        verbose_name = _("Face recognition photo")
        verbose_name_plural = _("Face recognition photos")
        ordering = ("photo",)


class FaceEncoding(models.Model):
    photo = models.ForeignKey(
        FaceRecognitionPhoto,
        verbose_name=_("Photo"),
        null=True,
        related_name="encodings",
        on_delete=models.CASCADE,
    )

    _field0 = models.FloatField()
    _field1 = models.FloatField()
    _field2 = models.FloatField()
    _field3 = models.FloatField()
    _field4 = models.FloatField()
    _field5 = models.FloatField()
    _field6 = models.FloatField()
    _field7 = models.FloatField()
    _field8 = models.FloatField()
    _field9 = models.FloatField()
    _field10 = models.FloatField()
    _field11 = models.FloatField()
    _field12 = models.FloatField()
    _field13 = models.FloatField()
    _field14 = models.FloatField()
    _field15 = models.FloatField()
    _field16 = models.FloatField()
    _field17 = models.FloatField()
    _field18 = models.FloatField()
    _field19 = models.FloatField()
    _field20 = models.FloatField()
    _field21 = models.FloatField()
    _field22 = models.FloatField()
    _field23 = models.FloatField()
    _field24 = models.FloatField()
    _field25 = models.FloatField()
    _field26 = models.FloatField()
    _field27 = models.FloatField()
    _field28 = models.FloatField()
    _field29 = models.FloatField()
    _field30 = models.FloatField()
    _field31 = models.FloatField()
    _field32 = models.FloatField()
    _field33 = models.FloatField()
    _field34 = models.FloatField()
    _field35 = models.FloatField()
    _field36 = models.FloatField()
    _field37 = models.FloatField()
    _field38 = models.FloatField()
    _field39 = models.FloatField()
    _field40 = models.FloatField()
    _field41 = models.FloatField()
    _field42 = models.FloatField()
    _field43 = models.FloatField()
    _field44 = models.FloatField()
    _field45 = models.FloatField()
    _field46 = models.FloatField()
    _field47 = models.FloatField()
    _field48 = models.FloatField()
    _field49 = models.FloatField()
    _field50 = models.FloatField()
    _field51 = models.FloatField()
    _field52 = models.FloatField()
    _field53 = models.FloatField()
    _field54 = models.FloatField()
    _field55 = models.FloatField()
    _field56 = models.FloatField()
    _field57 = models.FloatField()
    _field58 = models.FloatField()
    _field59 = models.FloatField()
    _field60 = models.FloatField()
    _field61 = models.FloatField()
    _field62 = models.FloatField()
    _field63 = models.FloatField()
    _field64 = models.FloatField()
    _field65 = models.FloatField()
    _field66 = models.FloatField()
    _field67 = models.FloatField()
    _field68 = models.FloatField()
    _field69 = models.FloatField()
    _field70 = models.FloatField()
    _field71 = models.FloatField()
    _field72 = models.FloatField()
    _field73 = models.FloatField()
    _field74 = models.FloatField()
    _field75 = models.FloatField()
    _field76 = models.FloatField()
    _field77 = models.FloatField()
    _field78 = models.FloatField()
    _field79 = models.FloatField()
    _field80 = models.FloatField()
    _field81 = models.FloatField()
    _field82 = models.FloatField()
    _field83 = models.FloatField()
    _field84 = models.FloatField()
    _field85 = models.FloatField()
    _field86 = models.FloatField()
    _field87 = models.FloatField()
    _field88 = models.FloatField()
    _field89 = models.FloatField()
    _field90 = models.FloatField()
    _field91 = models.FloatField()
    _field92 = models.FloatField()
    _field93 = models.FloatField()
    _field94 = models.FloatField()
    _field95 = models.FloatField()
    _field96 = models.FloatField()
    _field97 = models.FloatField()
    _field98 = models.FloatField()
    _field99 = models.FloatField()
    _field100 = models.FloatField()
    _field101 = models.FloatField()
    _field102 = models.FloatField()
    _field103 = models.FloatField()
    _field104 = models.FloatField()
    _field105 = models.FloatField()
    _field106 = models.FloatField()
    _field107 = models.FloatField()
    _field108 = models.FloatField()
    _field109 = models.FloatField()
    _field110 = models.FloatField()
    _field111 = models.FloatField()
    _field112 = models.FloatField()
    _field113 = models.FloatField()
    _field114 = models.FloatField()
    _field115 = models.FloatField()
    _field116 = models.FloatField()
    _field117 = models.FloatField()
    _field118 = models.FloatField()
    _field119 = models.FloatField()
    _field120 = models.FloatField()
    _field121 = models.FloatField()
    _field122 = models.FloatField()
    _field123 = models.FloatField()
    _field124 = models.FloatField()
    _field125 = models.FloatField()
    _field126 = models.FloatField()
    _field127 = models.FloatField()

    @property
    def encoding(self):
        return [getattr(self, f"_field{i}") for i in range(0, 128)]

    @encoding.setter
    def encoding(self, value):
        for i in range(0, 128):
            setattr(self, f"_field{i}", value[i])

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)

        if self.encoding:
            self.match_faces()

    def __str__(self):
        return f"Face encoding {self.id}"

    class Meta:
        verbose_name = _("Face encoding")
        verbose_name_plural = _("Face encodings")

    def match_faces(self):
        matches = (
            FaceEncoding.objects.filter(photo__isnull=True)
            .exclude(pk=self.pk)
            .extra(where=[face_recognition_distance_function(self.encoding)])
        )

        for reference_face in self.matches.all():
            if reference_face.encoding not in matches:
                self.matches.remove(reference_face)
        for encoding in matches.all():
            self.matches.add(encoding.reference_face)


def face_recognition_distance_function(encoding):
    distance_function = "sqrt("
    for i in range(0, 128):
        distance_function += f"power(_field{i} - {encoding[i]}, 2) + "
    distance_function = distance_function[0:-2] + "),"
    distance_function = distance_function[0:-1]
    return f"{distance_function} < 0.49"


def reference_face_uploadto(instance, filename):
    """Get path of file to upload to."""
    num = instance.member.reference_faces.all().count()
    extension = os.path.splitext(filename)[1]
    new_filename = str(num).zfill(4) + extension
    return os.path.join(
        "face_recognition/reference_faces", instance.member.username, new_filename
    )


class ReferenceFace(models.Model):
    member = models.ForeignKey(
        Member,
        verbose_name=_("Member"),
        on_delete=models.CASCADE,
        related_name="reference_faces",
    )
    encoding = models.OneToOneField(
        FaceEncoding,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reference_face",
    )
    file = models.ImageField(_("file"), upload_to=reference_face_uploadto)

    matches = models.ManyToManyField(FaceEncoding, related_name="matches")

    def match_photos(self):
        if not self.encoding:
            return

        matches = (
            FaceEncoding.objects.filter(photo__isnull=False)
            .exclude(pk=self.encoding.pk)
            .extra(where=[face_recognition_distance_function(self.encoding.encoding)])
        )
        for encoding in self.matches.all():
            if encoding not in matches:
                self.matches.remove(encoding)
        for encoding in matches:
            self.matches.add(encoding)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)
        if self.encoding:
            self.match_photos()

    def __str__(self):
        return str(self.file)

    def delete(self, using=None, keep_parents=False):
        removed = super().delete(using, keep_parents)
        if self.file.name:
            self.file.delete()
        return removed

    class Meta:
        verbose_name = _("Reference face")
        verbose_name_plural = _("Reference faces")
