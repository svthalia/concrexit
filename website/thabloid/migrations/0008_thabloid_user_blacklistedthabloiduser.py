# Generated by Django 4.1.3 on 2023-04-26 17:43

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import members.models.member


def populate_blacklistedthabloiduser(apps, schema_editor):
    Profile = apps.get_model("members", "Profile")
    BlacklistedThabloidUser = apps.get_model("thabloid", "BlacklistedThabloidUser")
    for profile in Profile.objects.filter(receive_magazine = False):
        BlacklistedThabloidUser.objects.create(thabloid_user=profile.user)

class Migration(migrations.Migration):

    dependencies = [
        ("members", "0037_profile_receive_magazine"),
        ("thabloid", "0007_thabloid_cover_alter_thabloid_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="Thabloid_user",
            fields=[],
            options={
                "verbose_name": "Thabloid user",
                "verbose_name_plural": "Thabloid users",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("members.member",),
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("current_members", members.models.member.CurrentMemberManager()),
                ("active_members", members.models.member.ActiveMemberManager()),
            ],
        ),
        migrations.CreateModel(
            name="BlacklistedThabloidUser",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "thabloid_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="thabloid.thabloid_user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Blacklisted Thabloid user",
                "verbose_name_plural": "Blacklisted Thabloid users",
            },
        ),
        migrations.RunPython(populate_blacklistedthabloiduser, migrations.RunPython.noop)
    ]
