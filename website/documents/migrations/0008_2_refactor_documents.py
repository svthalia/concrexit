from __future__ import unicode_literals
import os

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators

class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_1_refactor_documents'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='GeneralMeeting',
            name='minutes',
        ),

        migrations.DeleteModel(
            name='MiscellaneousDocument',
        ),

        migrations.DeleteModel(
            name='AssociationDocumentsYear',
        ),

        migrations.DeleteModel(
            name='GeneralMeetingDocument',
        ),

        migrations.CreateModel(
            name='MiscellaneousDocument',
            fields=[
            ],
            options={
                'verbose_name': 'Miscellaneous document',
                'verbose_name_plural': 'Miscellaneous documents',
                'proxy': True,
                'indexes': [],
            },
            bases=('documents.document',),
        ),
    ]
