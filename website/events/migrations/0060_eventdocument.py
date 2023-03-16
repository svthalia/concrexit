# Generated by Django 4.1.2 on 2023-03-15 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0017_delete_eventdocument"),
        ("activemembers", "0041_alter_membergroup_photo"),
        ("events", "0059_multiple_event_organisers"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventDocument",
            fields=[
                (
                    "document_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="documents.document",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="activemembers.membergroup",
                        verbose_name="owner",
                    ),
                ),
            ],
            options={
                "verbose_name": "event document",
                "verbose_name_plural": "event documents",
                "permissions": (
                    ("override_owner", "Can access event document as if owner"),
                ),
            },
            bases=("documents.document",),
        ),
    ]
