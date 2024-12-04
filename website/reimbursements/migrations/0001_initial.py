# Generated by Django 5.1.2 on 2024-12-04 18:57

import django.core.validators
import django.db.models.deletion
import payments.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('members', '0051_membership_study_long_until'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reimbursement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', payments.models.PaymentAmountField(decimal_places=2, help_text='How much did you pay (in euros)?', max_digits=8, validators=[payments.models.validate_not_zero])),
                ('date_incurred', models.DateField(help_text='When was this payment made?')),
                ('description', models.TextField(help_text='Why did you make this payment?', max_length=512, validators=[django.core.validators.MinLengthValidator(10)])),
                ('receipt', models.FileField(upload_to='receipts/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('verdict', models.CharField(blank=True, choices=[('approved', 'Approved'), ('denied', 'Denied')], max_length=40, null=True)),
                ('verdict_clarification', models.TextField(blank=True, help_text='Why did you choose this verdict?', null=True)),
                ('evaluated_at', models.DateTimeField(null=True)),
                ('evaluated_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reimbursements_approved', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reimbursements', to='members.member')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
