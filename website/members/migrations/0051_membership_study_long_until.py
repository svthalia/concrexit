import datetime
from django.utils import timezone
from django.db import migrations, models


def change_until(apps, schema_editor):
    Membership = apps.get_model("members", "Membership")

    new_until = datetime.datetime(
        year=timezone.now().year, month=9, day=1
    ) + datetime.timedelta(days=365)

    Membership.objects.filter(until=None, type=Membership.MEMBER).update(
        study_long=True, until=new_until.date()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0050_membership_study_long"),
    ]
    operations = [
        migrations.RunPython(change_until),
    ]
