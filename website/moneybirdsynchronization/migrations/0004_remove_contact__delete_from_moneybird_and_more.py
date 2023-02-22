# Generated by Django 4.1.7 on 2023-02-22 19:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0042_profile_is_minimized_alter_profile_address_city_and_more"),
        ("moneybirdsynchronization", "0003_rename_address1_contact_address_1_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contact",
            name="_delete_from_moneybird",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="_synced_with_moneybird",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="address_1",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="address_2",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="city",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="country",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="email",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="last_name",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="moneybird_version",
        ),
        migrations.RemoveField(
            model_name="contact",
            name="zipcode",
        ),
        migrations.AddField(
            model_name="contact",
            name="member",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="members.member",
                verbose_name="member",
            ),
        ),
        migrations.AlterField(
            model_name="contact",
            name="moneybird_id",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Moneybird ID"
            ),
        ),
    ]
