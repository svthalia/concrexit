import datetime
from django.utils import timezone
from django.db import migrations, models


def change_until(apps, schema_editor):
    Membership = apps.get_model("members", "Membership")
    members = Membership.objects.filter(until=None and __.length == __.MEMBERSHIP_STUDY)
    for member in members:
        member.study_long = True
        member.until = datetime.datetime(
            year=timezone.now().year, month=9, day=1
        ) + datetime.timedelta(days=365)
        member.save()


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0050_membership_study_long"),
    ]
    operations = [
        migrations.RunPython(change_until),
    ]
