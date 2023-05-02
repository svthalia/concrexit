import os
from secrets import token_urlsafe

from django.db import models
from django.db.models import Count, IntegerField, Max, Value
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from queryable_properties.properties import AnnotationProperty
from thumbnails.fields import ImageField

from members.models import Member
from photos.models import Photo


class FaceDetectionUser(Member):
    class Meta:
        proxy = True


def authentication_token() -> str:
    """Generate a 40 characters long base64 token suitable for authentication."""
    return token_urlsafe(30)


def reference_face_uploadto(instance, filename):
    """Get path of file to upload to."""
    random = token_urlsafe(6)
    extension = os.path.splitext(filename)[1]
    return os.path.join(
        "facedetection/reference-faces",
        f"{instance.user.username}-{random}{extension}",
    )


class BaseFaceEncodingSource(models.Model):
    """Abstract model for a source of face encodings."""

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        ERROR = "error", "Error"

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PROCESSING,
        help_text="Status of the encoding extraction process.",
    )

    token = models.CharField(
        max_length=40,
        default=token_urlsafe,
        editable=False,
        help_text="Token used by a Lambda to authenticate "
        "to the API to submit encoding(s) for this source.",
    )

    class Meta:
        abstract = True


class FaceDetectionPhoto(BaseFaceEncodingSource):
    """A source of face encodings from a Photo."""

    photo = models.OneToOneField(Photo, on_delete=models.CASCADE)

    num_faces = AnnotationProperty(
        Coalesce(Count("encodings"), Value(0), output__field=IntegerField())
    )


class ReferenceFace(BaseFaceEncodingSource):
    """A source of face encodings from a reference photo of a user's face.

    If a user marks a reference face for deletion, it will be kept for some
    time to allow us to monitor whether people searched for faces of others.
    """

    user = models.ForeignKey(
        FaceDetectionUser,
        on_delete=models.CASCADE,
        related_name="reference_faces",
    )
    file = ImageField(upload_to=reference_face_uploadto)

    marked_for_deletion_at = models.DateTimeField(null=True, blank=True)

    def delete(self, **kwargs):
        if self.file.name:
            self.file.delete()
        return super().delete(**kwargs)


class BaseFaceEncoding(models.Model):
    """Abstract model for a face encoding, without a source."""

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

    class Meta:
        abstract = True

    @cached_property
    def encoding(self) -> list[float]:
        [getattr(self, f"_field{i}") for i in range(0, 128)]

    @encoding.setter
    def encoding(self, value):
        for i in range(0, 128):
            setattr(self, f"_field{i}", value[i])

    def encoding_match_function(self) -> str:
        """Return a SQL expression that holds for encodings that match this one.

        Computes the Euclidean distance between this encoding and the other one,
        and checks whether it's less than a threshold of 0.49.
        """
        sum_of_squares = " + ".join(
            f"power(_field{i} - {self.encoding[i]}, 2)" for i in range(0, 128)
        )
        euclidean_distance = f"sqrt({sum_of_squares})"

        return f"{euclidean_distance} < 0.49"


class PhotoFaceEncoding(BaseFaceEncoding):
    """A face encoding found in a Photo."""

    photo = models.ForeignKey(
        FaceDetectionPhoto, on_delete=models.CASCADE, related_name="encodings"
    )

    def save(self, **kwargs):
        created = self.pk is None
        super().save(**kwargs)

        if created:
            self._set_matches()

    def _set_matches(self):
        """(Re-)compute the reference encodings that match this face."""
        matches = ReferenceFaceEncoding.objects.extra(
            where=[self.encoding_match_function()]
        )
        self.matches.set(matches)


class ReferenceFaceEncoding(BaseFaceEncoding):
    """The face encoding in a reference photo."""

    reference = models.OneToOneField(ReferenceFace, on_delete=models.CASCADE)

    matches = models.ManyToManyField(
        PhotoFaceEncoding,
        related_name="matches",
        editable=False,
    )

    def save(self, **kwargs):
        created = self.pk is None
        super().save(**kwargs)

        if created:
            self._set_matches()

    def _set_matches(self):
        """(Re-)compute the photo face encodings that match this reference."""
        matches = PhotoFaceEncoding.objects.extra(
            where=[self.encoding_match_function()]
        )
        self.matches.set(matches)
