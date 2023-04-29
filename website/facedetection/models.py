from django.db.models import models

from thumbnails.fields import ImageField

from members.models import Member
from photos.models import Photo


class FaceDetectionUser(Member):
    class Meta:
        proxy = True


class BaseFaceEncodingSource(models.Model):
    """Abstract model for a source of face encodings."""

    encoding_done = models.BooleanField(default=False)
    token = models.UUIDField()

    class Meta:
        abstract = True


class FaceEncodedPhoto(BaseFaceEncodingSource):
    """A source of face encodings from a Photo."""

    photo = models.OneToOneField(Photo)


class FaceReferencePhoto(BaseFaceEncodingSource):
    """A source of face encodings from a reference photo of a user's face."""

    user = models.ForeignKey(FaceDetectionUser, on_delete=models.CASCADE)
    file = ImageField()


class BaseFaceEncoding(models.Model):
    """Abstract model for a face encoding, without a source."""

    field0 = models.FloatField()
    field1 = models.FloatField()
    field2 = models.FloatField()
    field3 = models.FloatField()
    field4 = models.FloatField()
    field5 = models.FloatField()
    field6 = models.FloatField()
    field7 = models.FloatField()
    field8 = models.FloatField()
    field9 = models.FloatField()
    field10 = models.FloatField()
    field11 = models.FloatField()
    field12 = models.FloatField()
    field13 = models.FloatField()
    field14 = models.FloatField()
    field15 = models.FloatField()
    field16 = models.FloatField()
    field17 = models.FloatField()
    field18 = models.FloatField()
    field19 = models.FloatField()
    field20 = models.FloatField()
    field21 = models.FloatField()
    field22 = models.FloatField()
    field23 = models.FloatField()
    field24 = models.FloatField()
    field25 = models.FloatField()
    field26 = models.FloatField()
    field27 = models.FloatField()
    field28 = models.FloatField()
    field29 = models.FloatField()
    field30 = models.FloatField()
    field31 = models.FloatField()
    field32 = models.FloatField()
    field33 = models.FloatField()
    field34 = models.FloatField()
    field35 = models.FloatField()
    field36 = models.FloatField()
    field37 = models.FloatField()
    field38 = models.FloatField()
    field39 = models.FloatField()
    field40 = models.FloatField()
    field41 = models.FloatField()
    field42 = models.FloatField()
    field43 = models.FloatField()
    field44 = models.FloatField()
    field45 = models.FloatField()
    field46 = models.FloatField()
    field47 = models.FloatField()
    field48 = models.FloatField()
    field49 = models.FloatField()
    field50 = models.FloatField()
    field51 = models.FloatField()
    field52 = models.FloatField()
    field53 = models.FloatField()
    field54 = models.FloatField()
    field55 = models.FloatField()
    field56 = models.FloatField()
    field57 = models.FloatField()
    field58 = models.FloatField()
    field59 = models.FloatField()
    field60 = models.FloatField()
    field61 = models.FloatField()
    field62 = models.FloatField()
    field63 = models.FloatField()
    field64 = models.FloatField()
    field65 = models.FloatField()
    field66 = models.FloatField()
    field67 = models.FloatField()
    field68 = models.FloatField()
    field69 = models.FloatField()
    field70 = models.FloatField()
    field71 = models.FloatField()
    field72 = models.FloatField()
    field73 = models.FloatField()
    field74 = models.FloatField()
    field75 = models.FloatField()
    field76 = models.FloatField()
    field77 = models.FloatField()
    field78 = models.FloatField()
    field79 = models.FloatField()
    field80 = models.FloatField()
    field81 = models.FloatField()
    field82 = models.FloatField()
    field83 = models.FloatField()
    field84 = models.FloatField()
    field85 = models.FloatField()
    field86 = models.FloatField()
    field87 = models.FloatField()
    field88 = models.FloatField()
    field89 = models.FloatField()
    field90 = models.FloatField()
    field91 = models.FloatField()
    field92 = models.FloatField()
    field93 = models.FloatField()
    field94 = models.FloatField()
    field95 = models.FloatField()
    field96 = models.FloatField()
    field97 = models.FloatField()
    field98 = models.FloatField()
    field99 = models.FloatField()
    field100 = models.FloatField()
    field101 = models.FloatField()
    field102 = models.FloatField()
    field103 = models.FloatField()
    field104 = models.FloatField()
    field105 = models.FloatField()
    field106 = models.FloatField()
    field107 = models.FloatField()
    field108 = models.FloatField()
    field109 = models.FloatField()
    field110 = models.FloatField()
    field111 = models.FloatField()
    field112 = models.FloatField()
    field113 = models.FloatField()
    field114 = models.FloatField()
    field115 = models.FloatField()
    field116 = models.FloatField()
    field117 = models.FloatField()
    field118 = models.FloatField()
    field119 = models.FloatField()
    field120 = models.FloatField()
    field121 = models.FloatField()
    field122 = models.FloatField()
    field123 = models.FloatField()
    field124 = models.FloatField()
    field125 = models.FloatField()
    field126 = models.FloatField()
    field127 = models.FloatField()

    class Meta:
        abstract = True


class PhotoFaceEncoding(BaseFaceEncoding):
    """A face encoding found in a Photo."""

    photo = models.ForeignKey(FaceEncodedPhoto, on_delete=models.CASCADE)


class ReferenceFaceEncoding(BaseFaceEncoding):
    """The face encoding in a reference photo."""

    reference = models.OneToOneField(FaceReferencePhoto, on_delete=models.CASCADE)

    matches = models.ManyToManyField(PhotoFaceEncoding, related_name="matches")
