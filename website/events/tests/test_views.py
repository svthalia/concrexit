import datetime

from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.utils import timezone

from activemembers.models import Committee, CommitteeMembership
from events.models import Event, Registration, RegistrationInformationField
from members.models import Member


class AdminTest(TestCase):
    """Tests for admin views"""

    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            title_nl='testevenement',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(user__last_name="Wiggers").first()
        cls.permission_change_event = Permission.objects.get(
            content_type__model='event',
            codename='change_event')
        cls.member.user.user_permissions.add(cls.permission_change_event)
        cls.member.user.is_superuser = False
        cls.member.user.save()
        cls.committee = Committee.objects.get(pk=1)

    def setUp(self):
        self.client.force_login(self.member.user)

    def _remove_event_permission(self):
        self.member.user.user_permissions.remove(self.permission_change_event)

    def test_admin_details_need_change_event_access(self):
        """I need the event.change_event permission to do stuff"""
        self._remove_event_permission()
        response = self.client.get('/events/admin/1/')
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith('/login/'))

    def test_admin_details_no_organiser_allowed_access(self):
        """If an event has no organiser, then I should be allowed access"""
        response = self.client.get('/events/admin/1/')
        self.assertEqual(200, response.status_code)

    def test_admin_details_organiser_denied(self):
        self.event.organiser = self.committee
        self.event.save()
        response = self.client.get('/events/admin/1/')
        self.assertEqual(403, response.status_code)

    def test_admin_details_organiser_allowed(self):
        self.event.organiser = self.committee
        CommitteeMembership.objects.create(
            member=self.member,
            committee=self.committee)
        self.event.save()
        response = self.client.get('/events/admin/1/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_no_organiser_allowed(self):
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_allowed(self):
        """Test the ModelAdmin change page

        If I'm an organiser I should be allowed access
        """
        self.event.organiser = self.committee
        CommitteeMembership.objects.create(
            member=self.member,
            committee=self.committee)
        self.event.save()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_no_permissions_denied(self):
        """Test the ModelAdmin change page

        If I'm an organiser, but don't have perms I should not
        be allowed access
        """
        self._remove_event_permission()
        self.event.organiser = self.committee
        CommitteeMembership.objects.create(
            member=self.member,
            committee=self.committee)
        self.event.save()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(403, response.status_code)

    def test_modeladmin_change_superuser_allowed(self):
        """Test the ModelAdmin change page

        If I'm an organiser I should be allowed access
        """
        self.event.organiser = self.committee
        self.event.save()
        self.member.user.is_superuser = True
        self.member.user.save()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_denied(self):
        """Test the ModelAdmin change page

        If I'm not an organiser I should not be allowed access
        """
        self.event.organiser = self.committee
        self.event.save()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(403, response.status_code)


class RegistrationTest(TestCase):
    """Tests for registration view"""

    fixtures = ['members.json']

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            title_nl='testevene',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(user__last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member.user)

    def test_registration_register_not_required(self):
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 0)

    def test_registration_register(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 1)
        self.assertEqual(
                self.event.registration_set.first().member, self.member)

    def test_registration_register_twice(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 1)

    def test_registration_register_closed(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 0)

    def test_registration_cancel(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        Registration.objects.create(event=self.event, member=self.member)
        response = self.client.post('/events/1/registration/cancel/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 0)

    def test_registration_register_fields(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False)

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False)

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False)

        response = self.client.post('/events/1/registration/register/',
                                    {'info_field_1': True,
                                     'info_field_2': 42,
                                     'info_field_3': "text"},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.event.num_participants(), 1)
        registration = self.event.registration_set.first()
        self.assertEqual(field1.get_value_for(registration), True)
        self.assertEqual(field2.get_value_for(registration), 42)
        self.assertEqual(field3.get_value_for(registration), 'text')

    def test_registration_register_field_required(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        RegistrationInformationField.objects.create(
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test",
            name_nl="test",
            required=True)

        response = self.client.post('/events/1/registration/register/',
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates]
        self.assertIn('events/event_fields.html', template_names)
        self.assertEqual(self.event.num_participants(), 0)

        # This is wrong
        response = self.client.post('/events/1/registration/register/',
                                    {'test': 'test'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 0)

        # This is correct
        response = self.client.post('/events/1/registration/register/',
                                    {'info_field_1': 'test'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.num_participants(), 1)
