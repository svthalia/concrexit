# Generated by Django 4.1.2 on 2023-03-15 19:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0016_alter_document_members_only"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EventDocument",
        ),
    ]
