# Generated by Django 4.0.7 on 2022-11-11 21:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0041_alter_profile_photo'),
        ('facerecognition', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='referenceface',
            name='marked_for_deletion_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='marked for deletion at'),
        ),
        migrations.AlterField(
            model_name='faceencoding',
            name='photo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='encodings', to='facerecognition.facerecognitionphoto', verbose_name='Photo'),
        ),
        migrations.AlterField(
            model_name='referenceface',
            name='encoding',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reference_face', to='facerecognition.faceencoding', verbose_name='encoding'),
        ),
        migrations.AlterField(
            model_name='referenceface',
            name='matches',
            field=models.ManyToManyField(related_name='matches', to='facerecognition.faceencoding', verbose_name='matches'),
        ),
        migrations.AlterField(
            model_name='referenceface',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reference_faces', to='members.member', verbose_name='member'),
        ),
    ]
