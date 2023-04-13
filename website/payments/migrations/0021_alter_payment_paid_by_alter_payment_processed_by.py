# Generated by Django 4.2 on 2023-04-13 15:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0044_alter_profile_photo"),
        ("payments", "0020_alter_payment_paid_by_alter_payment_processed_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="paid_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="paid_payment_set",
                to="members.member",
                verbose_name="paid by",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="processed_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="processed_payment_set",
                to="members.member",
                verbose_name="processed by",
            ),
        ),
    ]