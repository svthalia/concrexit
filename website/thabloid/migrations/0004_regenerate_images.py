from django.db import migrations


def regenerate(apps, schema_editor):
    Thabloid = apps.get_model('thabloid', 'Thabloid')
    for thabloid in Thabloid.objects.all():
        thabloid.extract_thabloid_pages(True)


class Migration(migrations.Migration):

    dependencies = [
        ('thabloid', '0003_auto_20180307_2047'),
    ]

    operations = [
        migrations.RunPython(regenerate)
    ]
