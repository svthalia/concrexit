# Generated by Django 5.0.2 on 2024-03-20 22:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("newsletters", "0017_newsletter_rendered_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsletterevent",
            name="penalty_costs",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=None,
                help_text="This is the price that a member has to pay when he/she did not show up.",
                max_digits=8,
                null=True,
                verbose_name="Fine (in Euro)",
            ),
        ),
    ]