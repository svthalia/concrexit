# Generated by Django 5.0.2 on 2024-05-29 17:03

from django.db import migrations

def forward_func(apps, schema_editor):
    category = apps.get_model("pushnotifications", "Category")
    category.objects.create(key = "thabloid",
                            name = "Thabloid",
                            description="Notification when new Thabloid is uploaded")

class Migration(migrations.Migration):
    dependencies = [
        ("pushnotifications", "0022_remove_device_language"),
    ]

    operations = [
        migrations.RunPython(forward_func, migrations.RunPython.noop)
        ]