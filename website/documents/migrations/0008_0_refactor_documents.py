from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0007_auto_20160930_1447'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_nl', models.CharField(max_length=200, verbose_name='name (NL)')),
                ('name_en', models.CharField(max_length=200, verbose_name='name (EN)')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='last updated')),
                ('category', models.CharField(choices=[('annual', 'Annual document'), ('association', 'Association document'), ('minutes', 'Minutes'), ('misc', 'Miscellaneous document')], default='misc', max_length=40, verbose_name='category')),
                ('file_en', models.FileField(upload_to='documents/', validators=[utils.validators.validate_file_extension], verbose_name='file (EN)')),
                ('file_nl', models.FileField(upload_to='documents/', validators=[utils.validators.validate_file_extension], verbose_name='file (NL)')),
                ('members_only', models.BooleanField(default=False, verbose_name='members only')),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents'
            },
        ),

        migrations.CreateModel(
            name='AnnualDocument',
            fields=[
                ('document_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='documents.Document')),
                ('subcategory', models.CharField(choices=[('report', 'Annual report'), ('financial', 'Financial report'), ('policy', 'Policy document')], default='report', max_length=40, verbose_name='category')),
                ('year', models.IntegerField(validators=[django.core.validators.MinValueValidator(1990)], verbose_name='year')),
            ],
            options={
                'unique_together': {('subcategory', 'year')},
                'verbose_name': 'Annual document',
                'verbose_name_plural': 'Annual documents',
            },
            bases=('documents.document',),
        ),

        migrations.CreateModel(
            name='AssociationDocument',
            fields=[
            ],
            options={
                'verbose_name': 'Miscellaneous association document',
                'verbose_name_plural': 'Miscellaneous association documents',
                'proxy': True,
                'indexes': [],
            },
            bases=('documents.document',),
        ),

        migrations.RenameField(
            model_name='GeneralMeeting',
            old_name='minutes',
            new_name='minutes_old',
        ),

        migrations.CreateModel(
            name='Minutes',
            fields=[
                ('document_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='documents.Document')),
                ('meeting', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='documents.GeneralMeeting')),
            ],
            options={
                'verbose_name': 'Minutes',
                'verbose_name_plural': 'Minutes',
            },
            bases=('documents.document',),
        ),

        migrations.AddField(
            model_name='GeneralMeeting',
            name='documents',
            field=models.ManyToManyField(to='documents.Document', verbose_name='documents', blank=True),
        ),

        migrations.AlterField(
            model_name='GeneralMeeting',
            name='datetime',
            field=models.DateTimeField(verbose_name='datetime'),
        ),

        migrations.RenameField(
            model_name='GeneralMeeting',
            old_name='location',
            new_name='location_nl',
        ),

        migrations.AlterField(
            model_name='GeneralMeeting',
            name='location_nl',
            field=models.CharField(max_length=200, verbose_name='location (NL)'),
        ),

        migrations.AddField(
            model_name='GeneralMeeting',
            name='location_en',
            field=models.CharField(max_length=200, verbose_name='location (EN)', blank=True, null=True),
        ),

        migrations.AlterModelOptions(
            name='generalmeeting',
            options={'ordering': ['datetime'], 'verbose_name': 'General meeting', 'verbose_name_plural': 'General meetings'},
        ),
    ]
