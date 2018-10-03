from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy as _

from members.models import Member, Membership, Profile
from registrations.models import Entry, Registration, Renewal


class EntryTest(TestCase):
    fixtures = ['members.json']

    @classmethod
    def setUpTestData(cls):
        cls.registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            programme='computingscience',
            starting_year=2014,
            address_street='Heyendaalseweg 135',
            address_street2='',
            address_postal_code='6525AJ',
            address_city='Nijmegen',
            phone_number='06123456789',
            birthday=timezone.now().replace(year=1990),
            language='en',
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.renewal = Renewal(
            member=cls.member,
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
        )

    @mock.patch('django.db.models.Model.__str__')
    def test_str(self, str_mock):
        entry = Entry(registration=self.registration)
        self.assertEqual(str(entry), '{} {} ({})'.format(
            self.registration.first_name, self.registration.last_name,
            self.registration.email))

        entry = Entry(renewal=self.renewal)
        self.assertEqual(str(entry), '{} {} ({})'.format(
            self.member.first_name, self.member.last_name,
            self.member.email))

        str_mock.return_value = 'return str'
        entry = Entry()
        str(entry)
        str_mock.assert_called_once_with()


class RegistrationTest(TestCase):
    """Tests registrations"""

    @classmethod
    def setUpTestData(cls):
        cls.registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            programme='computingscience',
            starting_year=2014,
            address_street='Heyendaalseweg 135',
            address_street2='',
            address_postal_code='6525AJ',
            address_city='Nijmegen',
            phone_number='06123456789',
            student_number='s1234567',
            birthday=timezone.now().replace(year=1990),
            language='en',
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

    def setUp(self):
        translation.activate('en')
        self.registration.refresh_from_db()

    def test_str(self):
        self.assertEqual(str(self.registration), '{} {} ({})'.format(
            self.registration.first_name, self.registration.last_name,
            self.registration.email))

    def test_full_clean_works(self):
        self.registration.full_clean()

    def test_clean_works(self):
        self.registration.clean()

    def test_unique_email_user(self):
        self.registration.clean()
        user = get_user_model().objects.create_user('johnnydoe',
                                                    'johndoe@example.com')

        with self.assertRaises(ValidationError):
            self.registration.clean()

        user.delete()
        self.registration.clean()
        Registration.objects.create(
            first_name='John',
            last_name='Doe',
            birthday=timezone.now().replace(year=1990),
            email='johndoe@example.com',
        )

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_unique_student_number_user(self):
        self.registration.student_number = 's1234567'
        self.registration.clean()

        user = get_user_model().objects.create_user(
            'johnnydoe', 'johndoe2@example.com')
        Profile.objects.create(
            user=user,
            student_number='s1234567'
        )

        with self.assertRaises(ValidationError):
            self.registration.clean()

        user.delete()
        self.registration.clean()
        Registration.objects.create(
            first_name='John',
            last_name='Doe',
            birthday=timezone.now().replace(year=1990),
            student_number='s1234567'
        )

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_require_student_number_members(self):
        with self.subTest('No student number entered'):
            self.registration.student_number = None
            with self.assertRaisesMessage(
                    ValidationError,
                    "{'student_number': ['This field is required.']}"
            ):
                self.registration.clean()

        with self.subTest('Type is benefactor'):
            self.registration.student_number = None
            self.registration.membership_type = Membership.BENEFACTOR
            self.registration.clean()

    def test_unique_username_user(self):
        self.registration.username = 'johndoe'
        self.registration.clean()

        get_user_model().objects.create_user('johndoe',
                                             'johndoe@example.com')

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_require_programme_members(self):
        self.registration.programme = None
        with self.assertRaisesMessage(
                ValidationError,
                "{'programme': ['This field is required.']}"
        ):
            self.registration.clean()
        self.registration.membership_type = Membership.BENEFACTOR
        self.registration.clean()

    def test_require_starting_year_members(self):
        self.registration.starting_year = None
        with self.assertRaisesMessage(
                ValidationError,
                "{'starting_year': ['This field is required.']}"
        ):
            self.registration.clean()
        self.registration.membership_type = Membership.BENEFACTOR
        self.registration.clean()

    def test_save(self):
        registration = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            programme='computingscience',
            student_number='s1234567',
            starting_year=2014,
            address_street='Heyendaalseweg 135',
            address_street2='',
            address_postal_code='6525AJ',
            address_city='Nijmegen',
            phone_number='06123456789',
            birthday=timezone.now().replace(year=1990),
            language='en',
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
        )

        self.assertEqual(len(mail.outbox), 1)
        confirm_url = '{}{}'.format('https://thalia.nu',
                                    reverse('registrations:confirm-email',
                                            args=[registration.pk]))
        self.assertTrue(confirm_url in mail.outbox[0].body)
        mail.outbox.clear()

        registration.status = Entry.STATUS_REVIEW
        registration.save()

        self.assertEqual(len(mail.outbox), 0)


class RenewalTest(TestCase):
    fixtures = ['members.json']

    def setUp(self):
        self.member = Member.objects.filter(last_name="Wiggers").first()
        self.renewal = Renewal(
            member=self.member,
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
        )

    def test_str(self):
        self.assertEqual(str(self.renewal), '{} {} ({})'.format(
            self.member.first_name, self.member.last_name,
            self.member.email))

    def test_clean_works(self):
        self.member.membership_set.all().delete()
        self.renewal.clean()

    def test_existing_renewal_in_review(self):
        Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
        )

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertEqual(e.message, _('You already have a renewal '
                                          'request queued for review.'))

    def test_not_within_renew_period(self):
        membership = self.member.latest_membership
        membership.until = (timezone.now().date() +
                            timezone.timedelta(days=32))
        membership.save()

        self.renewal.length = Entry.MEMBERSHIP_YEAR

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(e.error_dict, {
                'length': 'You cannot renew your membership at this moment.',
            })

    def test_within_renew_period(self):
        self.renewal.length = Entry.MEMBERSHIP_YEAR

        membership = self.member.latest_membership
        membership.until = (timezone.now().date() +
                            timezone.timedelta(days=31))
        membership.save()

        self.renewal.clean()

    def test_benefactor_no_study_length(self):
        self.renewal.length = Entry.MEMBERSHIP_STUDY
        self.renewal.membership_type = Membership.BENEFACTOR
        membership = self.member.latest_membership
        membership.until = timezone.now()
        membership.save()

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(e.error_dict, {
                'length': 'Benefactors cannot have a membership '
                          'that lasts their entire study duration.',
            })

    def test_has_active_membership(self):
        membership = self.member.current_membership
        membership.until = None
        membership.save()

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(e.error_dict, {
                'length': 'You currently have an active membership.',
                'membership_type': 'You currently have an active membership.',
            })
