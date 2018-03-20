from __future__ import unicode_literals
import os

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators


def make_assocation_documents(apps, schema_editor):
    MiscellaneousDocument = apps.get_model('documents', 'MiscellaneousDocument')
    AssociationDocument = apps.get_model('documents', 'AssociationDocument')

    for doc in MiscellaneousDocument.objects.all():
        AssociationDocument.objects.create(
            name_en = doc.name,
            name_nl = doc.name,
            file_en = doc.file,
            file_nl = doc.file,
            members_only = doc.members_only,
            category = 'association',
        )


def make_annual_documents(apps, schema_editor):
    AssociationDocumentsYear = apps.get_model('documents', 'AssociationDocumentsYear')
    AnnualDocument = apps.get_model('documents', 'AnnualDocument')

    for year in AssociationDocumentsYear.objects.all():
        if year.policy_document:
            AnnualDocument.objects.create(
                name_en = 'Policy document %d' % year.year,
                name_nl = 'Beleidsdocument %d' % year.year,
                file_en = year.policy_document,
                file_nl = year.policy_document,
                members_only = True,
                category = 'annual',
                subcategory = 'policy',
                year = year.year,
            )

        if year.annual_report:
            AnnualDocument.objects.create(
                name_en = 'Annual report %d' % year.year,
                name_nl = 'Jaarverslag %d' % year.year,
                file_en = year.annual_report,
                file_nl = year.annual_report,
                members_only = True,
                category = 'annual',
                subcategory = 'report',
                year = year.year,
            )

        if year.financial_report:
            AnnualDocument.objects.create(
                name_en = 'Financial report %d' % year.year,
                name_nl = 'Financieel jaarverslag %d' % year.year,
                file = year.financial_report,
                members_only = True,
                category = 'annual',
                subcategory = 'financial',
                year = year.year,
            )


def make_general_meeting_documents(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    GeneralMeetingDocument = apps.get_model('documents', 'GeneralMeetingDocument')

    for meeting_doc in GeneralMeetingDocument.objects.all():
        name = os.path.basename(meeting_doc.file.name),
        doc = Document.objects.create(
            name_en = name,
            name_nl = name,
            category = 'misc',
            file_en = meeting_doc.file,
            file_nl = meeting_doc.file,
            members_only = True,
        )
        meeting_doc.meeting.documents.add(doc)


def make_minutes_documents(apps, schema_editor):
    GeneralMeeting = apps.get_model('documents', 'GeneralMeeting')
    Minutes = apps.get_model('documents', 'Minutes')
    
    for meeting in GeneralMeeting.objects.all():
        if meeting.minutes_old:
            Minutes.objects.create(
                name_en = 'Minutes %s' % str(meeting.datetime.date()),
                name_nl = 'Notulen %s' % str(meeting.datetime.date()),
                category = 'minutes',
                file_en = meeting.minutes_old,
                file_nl = meeting.minutes_old,
                members_only = True,
                meeting = meeting,
            )


def set_location_en_meetings(apps, schema_editor):
    GeneralMeeting = apps.get_model('documents', 'GeneralMeeting')

    for meeting in GeneralMeeting.objects.all():
        meeting.location_en = meeting.location_nl
        meeting.save()
        

class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_0_refactor_documents'),
    ]

    operations = [
        migrations.RunPython(
            make_assocation_documents
        ),
        migrations.RunPython(
            make_annual_documents
        ),
        migrations.RunPython(
            make_general_meeting_documents
        ),
        migrations.RunPython(
            make_minutes_documents
        ),
        migrations.RunPython(
            set_location_en_meetings
        ),
    ]
