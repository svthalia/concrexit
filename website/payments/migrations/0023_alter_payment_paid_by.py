# Generated by Django 4.2.5 on 2023-10-02 14:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0047_remove_profile_receive_magazine"),
        ("payments", "0022_alter_bankaccount_iban"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="paid_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="paid_payment_set",
                to="members.member",
                verbose_name="paid by",
            ),
        ),
    ]
