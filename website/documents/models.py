from django.db import models
from django.utils.translation import ugettext_lazy as _

import os

from utils.validators import validate_file_extension


def associationdocs_path(instance, filename):
    filename = instance.filetype + instance.year
    return 'documents/associationdocs/{0}'.format(filename)


def minutes_path(instance, filename):
    _, ext = os.path.splitext(filename)
    return 'documents/{}/minutes{}'.format(instance.datetime.date(), ext)


def general_meetingdocs_path(instance, filename):
    _, ext = os.path.splitext(filename)
    return 'documents/{}/files/'.format(instance.datetime.date(), filename)


class AssociationDocument(models.Model):
    name = models.CharField(max_length=200)
    year = models.IntegerField()
    file = models.FileField(
        upload_to=associationdocs_path,
        validators=[validate_file_extension],
    )
    FILETYPES = (
        ('policy_document', _("Policy document")),
        ('annual_report', _("Annual report")),
        ('financial_report', _("Financial report")),
    )
    filetype = models.CharField(
        max_length=16,
        choices=FILETYPES,
    )


class GenericDocument(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='documents/general/',
        validators=[validate_file_extension],
    )
    members_only = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class GeneralMeeting(models.Model):
    minutes = models.FileField(
        upload_to=minutes_path,
        validators=[validate_file_extension],
    )
    datetime = models.DateTimeField()
    location = models.CharField(max_length=200)


class GeneralMeetingDocument(models.Model):
    meeting = models.ForeignKey(GeneralMeeting, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=general_meetingdocs_path,
        validators=[validate_file_extension],
    )

    def __str__(self):
        return self.file.name
