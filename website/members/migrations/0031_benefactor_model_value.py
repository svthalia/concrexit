from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0030_benefactor_model_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='type',
            field=models.CharField(choices=[('member', 'Member'), ('benefactor', 'Benefactor'), ('honorary', 'Honorary Member')], max_length=40, verbose_name='Membership type'),
        ),
    ]
