from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.validators import validate_file_extension


class AssociationDocument(models.Model):
    year = models.IntegerField()
    file = models.FileField(
        upload_to='documents/association/',
        validators=[validate_file_extension],
    )
    FILETYPES = (
        ('policy-document', _("Policy document")),
        ('annual-report', _("Annual report")),
        ('financial-report', _("Financial report")),
    )
    filetype = models.CharField(
        max_length=16,
        choices=FILETYPES,
    )


class GenericDocument(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='documents/generic/',
        validators=[validate_file_extension],
    )
    members_only = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class GeneralMeeting(models.Model):
    minutes = models.FileField(
        upload_to='documents/meetings/minutes/',
        validators=[validate_file_extension],
    )
    datetime = models.DateTimeField()
    location = models.CharField(max_length=200)


class GeneralMeetingDocument(models.Model):
    meeting = models.ForeignKey(GeneralMeeting, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='documents/meetings/files/',
        validators=[validate_file_extension],
    )

    def __str__(self):
        return self.file.name
