from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from members.models import Member
from payments import services
from payments.models import BankAccount


@freeze_time('2019-01-01')
@override_settings(SUSPEND_SIGNALS=True)
class ServicesTest(TestCase):
    """
    Test for the services
    """
    fixtures = ['members.json']

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def test_update_last_used(self):
        BankAccount.objects.create(
            owner=self.member,
            initials='J',
            last_name='Test',
            iban='NL91ABNA0417164300',
            mandate_no='11-1',
            valid_from=timezone.now().date() - timezone.timedelta(days=2000),
            valid_until=timezone.now().date() - timezone.timedelta(days=1500),
            signature='base64,png'
        )
        BankAccount.objects.create(
            owner=self.member,
            initials='J',
            last_name='Test',
            iban='NL91ABNA0417164300',
            mandate_no='11-2',
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            last_used=timezone.now().date() - timezone.timedelta(days=5),
            signature='base64,png'
        )

        self.assertEqual(
            services.update_last_used(BankAccount.objects),
            1
        )

        self.assertEqual(
            BankAccount.objects.filter(mandate_no='11-2').first().last_used,
            timezone.now().date()
        )

        self.assertEqual(
            services.update_last_used(
                BankAccount.objects,
                timezone.datetime(year=2018, month=12, day=12)
            ),
            1
        )

        self.assertEqual(
            BankAccount.objects.filter(mandate_no='11-2').first().last_used,
            timezone.datetime(year=2018, month=12, day=12).date()
        )

    def test_revoke_old_mandates(self):
        BankAccount.objects.create(
            owner=self.member,
            initials='J',
            last_name='Test1',
            iban='NL91ABNA0417164300',
            mandate_no='11-1',
            valid_from=timezone.now().date() - timezone.timedelta(days=2000),
            last_used=timezone.now().date() - timezone.timedelta(days=2000),
            signature='base64,png'
        )
        BankAccount.objects.create(
            owner=self.member,
            initials='J',
            last_name='Test2',
            iban='NL91ABNA0417164300',
            mandate_no='11-2',
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            last_used=timezone.now().date() - timezone.timedelta(days=5),
            signature='base64,png'
        )

        self.assertEqual(
            BankAccount.objects.filter(valid_until=None).count(),
            2
        )

        services.revoke_old_mandates()

        self.assertEqual(
            BankAccount.objects.filter(valid_until=None).count(),
            1
        )
