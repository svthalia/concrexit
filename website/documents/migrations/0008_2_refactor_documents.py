from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_1_refactor_documents'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='GeneralMeeting',
            name='minutes_old',
        ),

        migrations.AlterField(
            model_name='GeneralMeeting',
            name='location_en',
            field=models.CharField(max_length=200, verbose_name='location (EN)'),
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
