from django.db import migrations
from django.utils import timezone


def forwards_func(apps, schema_editor):
    Member = apps.get_model('members', 'profile')
    BankAccount = apps.get_model('payments', 'BankAccount')
    db_alias = schema_editor.connection.alias
    for profile in Member.objects.using(db_alias).exclude(
            bank_account=None).all():
        BankAccount.objects.using(db_alias).create(
            owner=profile.user,
            initials=profile.initials or profile.user.first_name[0],
            last_name=profile.user.last_name,
            valid_from=timezone.now(),
            mandate_no=f'{profile.user.pk}-1',
            signature="data:image/png;base64,",
            iban=profile.bank_account
        )


def reverse_func(apps, schema_editor):
    BankAccount = apps.get_model('payments', 'BankAccount')
    db_alias = schema_editor.connection.alias
    for account in BankAccount.objects.using(db_alias).all():
        account.owner.profile.bank_account = account.iban
        account.owner.profile.save()
        account.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('members', '0031_benefactor_model_value'),
        ('payments', '0004_bankaccount'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
