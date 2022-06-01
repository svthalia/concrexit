# Generated by Django 4.0.4 on 2022-06-01 17:24

from django.db import migrations, models
import django.db.models.manager
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='promotionrequest',
            managers=[
                ('upcoming_requests', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='promotionrequest',
            name='publish_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Publish date'),
        ),
    ]
