# Generated by Django 4.0.5 on 2022-06-08 19:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0041_alter_profile_photo'),
        ('photos', '0015_kudo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.member')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='photos.photo')),
            ],
        ),
        migrations.DeleteModel(
            name='Kudo',
        ),
    ]
