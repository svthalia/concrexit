import datetime

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from activemembers.models import Committee, MemberGroupMembership
from events.models import (
    Event,
    EventRegistration,
    RegistrationInformationField,
    BooleanRegistrationInformation,
    IntegerRegistrationInformation,
    TextRegistrationInformation,
)
from mailinglists.models import MailingList
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class AdminTest(TestCase):
    """Tests for admin views."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
        )
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.permission_change_event = Permission.objects.get(
            content_type__model="event", codename="change_event"
        )
        cls.permission_override_orga = Permission.objects.get(
            content_type__model="event", codename="override_organiser"
        )
        cls.member.user_permissions.add(cls.permission_change_event)
        cls.member.is_superuser = False
        cls.member.save()

    def setUp(self):
        self.client.force_login(self.member)

    def _remove_event_permission(self):
        self.member.user_permissions.remove(self.permission_change_event)

    def _add_override_organiser_permission(self):
        self.member.user_permissions.add(self.permission_override_orga)

    def test_admin_details_need_change_event_access(self):
        """I need the event.change_event permission to do stuff."""
        self._remove_event_permission()
        response = self.client.get("/admin/events/event/1/details/")
        self.assertEqual(403, response.status_code)

    def test_admin_details_organiser_denied(self):
        response = self.client.get("/admin/events/event/1/details/")
        self.assertEqual(403, response.status_code)

    def test_admin_details_organiser_allowed(self):
        MemberGroupMembership.objects.create(member=self.member, group=self.committee)
        response = self.client.get("/admin/events/event/1/details/")
        self.assertEqual(200, response.status_code)

    def test_admin_details_override_organiser_allowed(self):
        self._add_override_organiser_permission()
        response = self.client.get("/admin/events/event/1/details/")
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_allowed(self):
        """Change event as an organiser

        If I'm an organiser I should be allowed access
        """
        MemberGroupMembership.objects.create(member=self.member, group=self.committee)
        response = self.client.get("/admin/events/event/1/change/")
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_override_organiser_allowed(self):
        """Test the override organiser permission for changing events

        If I'm allowed to override organiser restrictions..
        """
        self._add_override_organiser_permission()
        response = self.client.get("/admin/events/event/1/change/")
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_no_permissions_denied(self):
        """Committee members without change permissions are banned

        If I'm an organiser, but don't have perms I should not
        be allowed access
        """
        self._remove_event_permission()
        MemberGroupMembership.objects.create(member=self.member, group=self.committee)
        response = self.client.get("/admin/events/event/1/change/")
        self.assertEqual(403, response.status_code)

    def test_modeladmin_change_superuser_allowed(self):
        """Superuser should be allowed access always."""
        self.member.is_superuser = True
        self.member.save()
        response = self.client.get("/admin/events/event/1/change/")
        self.assertEqual(200, response.status_code)
        self.assertIn("Change event", str(response.content))

    def test_modeladmin_change_organiser_denied(self):
        """If I'm not an organiser I should not be allowed access."""
        response = self.client.get("/admin/events/event/1/change/")
        self.assertEqual(200, response.status_code)
        self.assertIn("View event", str(response.content))

    def test_mark_present_qr_organiser_denied(self):
        response = self.client.get("/admin/events/event/1/mark-present-qr/")
        self.assertEqual(403, response.status_code)

    def test_mark_present_qr_organiser_allowed(self):
        MemberGroupMembership.objects.create(member=self.member, group=self.committee)
        response = self.client.get("/admin/events/event/1/mark-present-qr/")
        self.assertEqual(200, response.status_code)

    def test_mark_present_qr_override_organiser_allowed(self):
        self._add_override_organiser_permission()
        response = self.client.get("/admin/events/event/1/mark-present-qr/")
        self.assertEqual(200, response.status_code)


@override_settings(SUSPEND_SIGNALS=True)
class RegistrationTest(TestCase):
    """Tests for registration view."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.mailinglist = MailingList.objects.create(name="testmail")
        cls.committee = Committee.objects.create(
            name="committee",
            contact_mailinglist=cls.mailinglist,
        )
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
        )
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.mark_present_url = reverse(
            "events:mark-present",
            kwargs={
                "pk": cls.event.pk,
                "token": cls.event.mark_present_url_token,
            },
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member)

    def test_registration_register_not_required(self):
        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 1)
        self.assertEqual(self.event.eventregistration_set.first().member, self.member)

    def test_registration_register_twice(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_closed(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_cancel(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        EventRegistration.objects.create(event=self.event, member=self.member)
        response = self.client.post("/events/1/registration/cancel/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_register_no_fields(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name="test text",
            required=False,
        )

        response = self.client.post(
            "/events/1/registration/register/",
            {"info_field_1": True, "info_field_2": 42, "info_field_3": "text"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.event.participants.count(), 1)
        registration = self.event.eventregistration_set.first()
        self.assertEqual(field1.get_value_for(registration), None)
        self.assertEqual(field2.get_value_for(registration), None)
        self.assertEqual(field3.get_value_for(registration), None)

    def test_registration_missing_fields(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name="test bool",
            required=False,
        )

        RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name="test int",
            required=False,
        )

        RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name="test text",
            required=False,
        )

        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates]
        self.assertIn("events/registration.html", template_names)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_fields_required(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        RegistrationInformationField.objects.create(
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name="test",
            required=True,
        )

        response = self.client.post("/events/1/registration/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates]
        self.assertIn("events/registration.html", template_names)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_update_form_load_not_changes_fields(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name="test text",
            required=False,
        )

        registration = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        BooleanRegistrationInformation.objects.create(
            registration=registration, field=field1, value=True
        )
        IntegerRegistrationInformation.objects.create(
            registration=registration, field=field2, value=42
        )
        TextRegistrationInformation.objects.create(
            registration=registration, field=field3, value="text"
        )

        # as if there is a csrf token
        response = self.client.get("/events/1/registration/", follow=True)
        self.assertEqual(response.status_code, 200)

        registration = self.event.eventregistration_set.first()
        self.assertEqual(field1.get_value_for(registration), True)
        self.assertEqual(field2.get_value_for(registration), 42)
        self.assertEqual(field3.get_value_for(registration), "text")

    def test_registration_update_form_post_changes_fields(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name="test text",
            required=False,
        )

        response = self.client.post(
            "/events/1/registration/register/",
            {
                "info_field_1": True,
                "info_field_2": 42,
                "info_field_3": "text",
                "csrf": "random",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/events/1/registration/",
            {
                "info_field_1": False,
                "info_field_2": 1337,
                "info_field_3": "no text",
                "csrf": "random",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.event.participants.count(), 1)
        registration = self.event.eventregistration_set.first()
        self.assertEqual(field1.get_value_for(registration), False)
        self.assertEqual(field2.get_value_for(registration), 1337)
        self.assertEqual(field3.get_value_for(registration), "no text")

    def test_registration_cancel_after_deadline_notification(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.event.send_cancel_email = True
        self.event.save()
        EventRegistration.objects.create(event=self.event, member=self.member)
        response = self.client.post("/events/1/registration/cancel/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            [self.event.organiser.contact_mailinglist.name + "@thalia.nu"],
        )

    def test_registration_cancel_after_deadline_warning(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.event.save()
        EventRegistration.objects.create(event=self.event, member=self.member)
        response = self.client.get("/events/1/")
        self.assertContains(
            response,
            "Cancellation isn&#x27;t possible anymore without having to pay the full costs of",
        )

    def test_registration_cancel_after_deadline_waitinglist_no_warning(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.event.max_participants = 1
        self.event.save()
        EventRegistration.objects.create(
            event=self.event,
            member=Member.objects.get(pk=2),
            date=timezone.now() - datetime.timedelta(hours=1),
        )
        queue_register = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        response = self.client.get("/events/1/")
        self.assertTrue(queue_register in self.event.queue)
        self.assertNotContains(
            response,
            "Cancellation isn't possible anymore without having to pay the full costs of",
        )

    def test_mark_present_url_registered(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=1),
        )

        response = self.client.get(self.mark_present_url, follow=True)
        self.assertContains(response, "You have been marked as present.")
        registration.refresh_from_db()
        self.assertTrue(registration.present)

    def test_mark_present_url_registered(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=1),
            present=True,
        )

        response = self.client.get(self.mark_present_url, follow=True)
        self.assertContains(response, "You were already marked as present.")
        registration.refresh_from_db()
        self.assertTrue(registration.present)

    def test_mark_present_url_not_registered(self):
        response = self.client.get(self.mark_present_url, follow=True)
        self.assertContains(response, "You are not registered for this event.")

    def test_mark_present_url_wrong_token(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=3),
        )
        response = self.client.get(
            reverse(
                "events:mark-present",
                kwargs={
                    "pk": self.event.pk,
                    "token": "11111111-2222-3333-4444-555555555555",
                },
            ),
            follow=True,
        )

        self.assertContains(response, "Invalid url.")
        self.assertFalse(registration.present)

    def test_mark_present_url_past_event(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=3),
        )
        self.event.start = timezone.now() - datetime.timedelta(hours=2)
        self.event.end = timezone.now() - datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.get(self.mark_present_url, follow=True)

        self.assertContains(response, "This event has already ended.")
        self.assertFalse(registration.present)
