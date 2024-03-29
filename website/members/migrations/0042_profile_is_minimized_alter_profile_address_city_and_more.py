# Generated by Django 4.1.5 on 2023-01-25 19:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0041_alter_profile_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_minimized",
            field=models.BooleanField(
                default=False,
                verbose_name="The data from this profile has been minimized",
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="address_city",
            field=models.CharField(
                blank=True, max_length=40, null=True, verbose_name="City"
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="address_country",
            field=models.CharField(
                blank=True,
                choices=[
                    ("AX", "Åland Islands"),
                    ("AL", "Albania"),
                    ("AD", "Andorra"),
                    ("AT", "Austria"),
                    ("BY", "Belarus"),
                    ("BE", "Belgium"),
                    ("BA", "Bosnia and Herzegovina"),
                    ("BG", "Bulgaria"),
                    ("HR", "Croatia"),
                    ("CZ", "Czechia"),
                    ("DK", "Denmark"),
                    ("EE", "Estonia"),
                    ("FO", "Faroe Islands"),
                    ("FI", "Finland"),
                    ("FR", "France"),
                    ("DE", "Germany"),
                    ("GI", "Gibraltar"),
                    ("GR", "Greece"),
                    ("GG", "Guernsey"),
                    ("VA", "Vatican City"),
                    ("HU", "Hungary"),
                    ("IS", "Iceland"),
                    ("IE", "Ireland"),
                    ("IM", "Isle of Man"),
                    ("IT", "Italy"),
                    ("JE", "Jersey"),
                    ("LV", "Latvia"),
                    ("LI", "Liechtenstein"),
                    ("LT", "Lithuania"),
                    ("LU", "Luxembourg"),
                    ("MK", "Macedonia (FYROM)"),
                    ("MT", "Malta"),
                    ("MD", "Moldova"),
                    ("MC", "Monaco"),
                    ("ME", "Montenegro"),
                    ("NL", "Netherlands"),
                    ("NO", "Norway"),
                    ("PL", "Poland"),
                    ("PT", "Portugal"),
                    ("RO", "Romania"),
                    ("RU", "Russian Federation"),
                    ("SM", "San Marino"),
                    ("RS", "Serbia"),
                    ("SK", "Slovakia"),
                    ("SI", "Slovenia"),
                    ("ES", "Spain"),
                    ("SJ", "Svalbard and Jan Mayen"),
                    ("SE", "Sweden"),
                    ("CH", "Switzerland"),
                    ("UA", "Ukraine"),
                    ("GB", "United Kingdom"),
                ],
                max_length=2,
                null=True,
                verbose_name="Country",
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="address_postal_code",
            field=models.CharField(
                blank=True, max_length=10, null=True, verbose_name="Postal code"
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="address_street",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="please use the format <street> <number>",
                        regex="^.+ \\d+.*",
                    )
                ],
                verbose_name="Street and house number",
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="birthday",
            field=models.DateField(blank=True, null=True, verbose_name="Birthday"),
        ),
    ]
