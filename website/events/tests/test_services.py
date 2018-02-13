from datetime import timedelta, datetime
from unittest import mock

from django.contrib.auth.models import AnonymousUser, Permission
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from activemembers.models import Committee, CommitteeMembership
from events import services
from events.exceptions import RegistrationError
from events.models import Event, Registration, RegistrationInformationField
from members.models import Member


@freeze_time('2017-01-01')
class ServicesTest(TestCase):
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title_nl='testevenement',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + timedelta(hours=1)),
            end=(timezone.now() + timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.member.is_superuser = False
        cls.member.save()

        cls.perm_change_event = Permission.objects.get(
            content_type__model='event',
            codename='change_event')
        cls.perm_override_organiser = Permission.objects.get(
            content_type__model='event',
            codename='override_organiser')

    def setUp(self):
        self.committee.refresh_from_db()
        self.event.refresh_from_db()
        self.member.refresh_from_db()

    def _toggle_event_change_perm(self, enable):
        # Refetch member to empty permissions cache
        self.member = Member.objects.get(pk=self.member.pk)
        if enable:
            self.member.user_permissions.add(self.perm_change_event)
        else:
            self.member.user_permissions.remove(self.perm_change_event)

    def _toggle_override_organiser_perm(self, enable):
        # Refetch member to empty permissions cache
        self.member = Member.objects.get(pk=self.member.pk)
        if enable:
            self.member.user_permissions.add(self.perm_override_organiser)
        else:
            self.member.user_permissions.remove(self.perm_override_organiser)

    def test_is_user_registered(self):
        self.assertEqual(None, services.is_user_registered(AnonymousUser(),
                                                           self.event))
        self.event.registration_start = timezone.now() - timedelta(hours=1)
        self.event.registration_end = timezone.now()
        self.assertEqual(None, services.is_user_registered(AnonymousUser(),
                                                           self.event))
        self.assertFalse(services.is_user_registered(self.member,
                                                     self.event))
        Registration.objects.create(
            event=self.event,
            member=self.member,
            date_cancelled=None
        )

        self.assertTrue(services.is_user_registered(self.member,
                                                    self.event))

    def test_event_permissions(self):
        self.event.registration_start = timezone.now() - timedelta(hours=1)
        self.event.registration_end = timezone.now() + timedelta(hours=1)

        self.assertEqual({
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }, services.event_permissions(AnonymousUser(), self.event))

        self.member.profile.event_permissions = 'nothing'

        self.assertEqual({
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }, services.event_permissions(self.member, self.event))

        self.member.profile.event_permissions = 'all'

        self.assertEqual({
            "create_registration": True,
            "cancel_registration": False,
            "update_registration": False,
        }, services.event_permissions(self.member, self.event))

        reg = Registration.objects.create(
            event=self.event,
            member=self.member,
            date_cancelled=None
        )

        self.assertEqual({
            "create_registration": False,
            "cancel_registration": True,
            "update_registration": False,
        }, services.event_permissions(self.member, self.event))

        RegistrationInformationField.objects.create(
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_nl='test',
            name_en='test',
            required=False
        )

        self.assertEqual({
            "create_registration": False,
            "cancel_registration": True,
            "update_registration": True,
        }, services.event_permissions(self.member, self.event))

        reg.date_cancelled = timezone.now()
        reg.save()

        self.assertEqual({
            "create_registration": True,
            "cancel_registration": False,
            "update_registration": False,
        }, services.event_permissions(self.member, self.event))

    def test_is_organiser(self):
        self.assertFalse(services.is_organiser(AnonymousUser(), self.event))

        self.assertFalse(services.is_organiser(self.member, self.event))
        self.member.is_superuser = True
        self.assertTrue(services.is_organiser(self.member, self.event))
        self.member.is_superuser = False

        self._toggle_override_organiser_perm(True)
        self.assertTrue(services.is_organiser(self.member, self.event))
        self._toggle_override_organiser_perm(False)

        self._toggle_event_change_perm(True)
        self.assertFalse(services.is_organiser(self.member, self.event))
        membership = CommitteeMembership.objects.create(
            member=self.member, committee=self.committee)
        self.assertTrue(services.is_organiser(self.member, self.event))
        self.assertFalse(services.is_organiser(self.member, None))
        self._toggle_event_change_perm(False)
        membership.delete()

    @mock.patch('events.services.event_permissions')
    def test_create_registration(self, perms_mock):
        self.event.registration_start = timezone.now() - timedelta(hours=2)
        self.event.registration_end = timezone.now() + timedelta(hours=1)

        perms_mock.return_value = {
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }

        with self.assertRaises(RegistrationError):
            services.create_registration(AnonymousUser(), self.event)

        perms_mock.return_value["create_registration"] = True

        reg = services.create_registration(self.member, self.event)
        self.assertEqual(reg.event, self.event)
        self.assertEqual(reg.member, self.member)
        self.assertEqual(reg.date_cancelled, None)

        reg.date_cancelled = timezone.make_aware(datetime(2017, 9, 1))
        reg.save()

        reg = services.create_registration(self.member, self.event)
        self.assertEqual(reg.event, self.event)
        self.assertEqual(reg.member, self.member)
        self.assertEqual(reg.date_cancelled, None)

        self.event.cancel_deadline = timezone.now() - timedelta(hours=1)
        self.event.save()

        reg.date_cancelled = timezone.now()
        reg.save()

        with self.assertRaises(RegistrationError):
            services.create_registration(self.member, self.event)

        reg.date_cancelled = None
        reg.save()

        services.create_registration(self.member, self.event)

        perms_mock.return_value["create_registration"] = False
        perms_mock.return_value["cancel_registration"] = True

        with self.assertRaises(RegistrationError):
            services.create_registration(self.member, self.event)

    @mock.patch('events.emails.notify_organiser')
    @mock.patch('events.emails.notify_first_waiting')
    @mock.patch('events.services.event_permissions')
    def test_cancel_registration(self, perms_mock, notify_first_mock,
                                 notify_organiser_mock):
        self.event.registration_start = timezone.now() - timedelta(hours=2)
        self.event.registration_end = timezone.now() + timedelta(hours=1)
        self.event.max_participants = 1
        self.event.save()

        perms_mock.return_value = {
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }

        with self.assertRaises(RegistrationError):
            services.cancel_registration(None, self.member, self.event)

        registration = Registration.objects.create(
            event=self.event,
            member=self.member,
        )

        with self.assertRaises(RegistrationError):
            services.cancel_registration(None, self.member, self.event)

        perms_mock.return_value["cancel_registration"] = True

        services.cancel_registration(None, self.member, self.event)
        notify_first_mock.assert_called_once_with(None, self.event)

        self.event.send_cancel_email = True
        self.event.save()

        services.cancel_registration(None, self.member, self.event)

        self.event.cancel_deadline = timezone.make_aware(datetime(2017, 1, 1))
        self.event.save()

        services.cancel_registration(None, self.member, self.event)
        notify_organiser_mock.assert_called_once_with(self.event, registration)

        registration.refresh_from_db()
        self.assertIsNotNone(registration.date_cancelled)
        registration.date_cancelled = None
        registration.save()

        Registration.objects.create(
            event=self.event,
            member=Member.objects.filter(username="testuser").first(),
            date=timezone.make_aware(datetime(2017, 9, 1))
        )

        services.cancel_registration(None, self.member, self.event)

    @mock.patch('events.services.event_permissions')
    def test_update_registration(self, perms_mock):
        self.event.registration_start = timezone.now() - timedelta(hours=2)
        self.event.registration_end = timezone.now() + timedelta(hours=1)

        perms_mock.return_value = {
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }

        with self.assertRaises(RegistrationError):
            services.update_registration(self.member, self.event, None)

        registration = Registration.objects.create(
            event=self.event,
            member=self.member,
        )

        services.update_registration(self.member, self.event, None)

        perms_mock.return_value["update_registration"] = True

        field1 = RegistrationInformationField.objects.create(
            type=RegistrationInformationField.INTEGER_FIELD,
            event=self.event,
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            type=RegistrationInformationField.BOOLEAN_FIELD,
            event=self.event,
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            type=RegistrationInformationField.TEXT_FIELD,
            event=self.event,
            required=False,
        )

        fields = [
            ('info_field_{}'.format(field1.id), None),
            ('info_field_{}'.format(field2.id), None),
            ('info_field_{}'.format(field3.id), None),
        ]

        services.update_registration(self.member, self.event, fields)

        self.assertEqual(field1.get_value_for(registration), 0)
        self.assertEqual(field2.get_value_for(registration), False)
        self.assertEqual(field3.get_value_for(registration), '')

        fields = [
            ('info_field_{}'.format(field1.id), 2),
            ('info_field_{}'.format(field2.id), True),
            ('info_field_{}'.format(field3.id), 'text'),
        ]

        services.update_registration(self.member, self.event, fields)

        self.assertEqual(field1.get_value_for(registration), 2)
        self.assertEqual(field2.get_value_for(registration), True)
        self.assertEqual(field3.get_value_for(registration), 'text')

        field1.delete()
        field2.delete()
        field3.delete()

    @mock.patch('events.services.event_permissions')
    def test_registration_fields(self, perms_mock):
        perms_mock.return_value = {
            "create_registration": False,
            "cancel_registration": False,
            "update_registration": False,
        }

        with self.assertRaises(RegistrationError):
            services.registration_fields(self.member, self.event)

        Registration.objects.create(
            event=self.event,
            member=self.member,
        )

        with self.assertRaises(RegistrationError):
            services.registration_fields(self.member, self.event)

        perms_mock.return_value["update_registration"] = True

        RegistrationInformationField.objects.create(
            id=1,
            type=RegistrationInformationField.INTEGER_FIELD,
            event=self.event,
            required=False,
        )

        RegistrationInformationField.objects.create(
            id=2,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            event=self.event,
            required=True,
        )

        RegistrationInformationField.objects.create(
            id=3,
            type=RegistrationInformationField.TEXT_FIELD,
            event=self.event,
            required=False,
        )

        fields = services.registration_fields(self.member, self.event)

        self.assertEqual(fields['info_field_1'], {
            'type': 'integer',
            'label': '',
            'description': None,
            'value': None,
            'required': False
        })

        self.assertEqual(fields['info_field_2'], {
            'type': 'boolean',
            'label': '',
            'description': None,
            'value': None,
            'required': True
        })

        self.assertEqual(fields['info_field_3'], {
            'type': 'text',
            'label': '',
            'description': None,
            'value': None,
            'required': False
        })

        self.assertEqual(len(fields), 3)
