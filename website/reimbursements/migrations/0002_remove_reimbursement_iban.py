# Generated by Django 5.1.2 on 2025-03-14 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reimbursements', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reimbursement',
            name='iban',
        ),
    ]
