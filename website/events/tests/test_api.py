import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from activemembers.models import Committee
from events.models import (
    BooleanRegistrationInformation,
    Event,
    EventRegistration,
    IntegerRegistrationInformation,
    RegistrationInformationField,
    TextRegistrationInformation,
)
from events.models.external_event import ExternalEvent
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class RegistrationApiTest(TestCase):
    """Tests for registration view."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=13.37,
            fine=5.00,
        )
        cls.event.organisers.add(Committee.objects.get(pk=1))
        cls.member = Member.objects.filter(last_name="Wiggers").first()

        cls.mark_present_api_url = reverse(
            "api:v2:events:mark-present",
            kwargs={
                "pk": cls.event.pk,
                "token": cls.event.mark_present_url_token,
            },
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_registration_register_not_required(self):
        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)
        self.assertEqual(self.event.participants.count(), 1)
        self.assertEqual(self.event.eventregistration_set.first().member, self.member)

    def test_registration_register_twice(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)
        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_closed(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_cancel(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        reg = EventRegistration.objects.create(event=self.event, member=self.member)
        response = self.client.delete(
            f"/api/v2/events/1/registrations/{reg.pk}/", follow=True
        )
        self.assertEqual(response.status_code, 204)
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
            "/api/v2/events/1/registrations/",
            {"info_field_1": True, "info_field_2": 42, "info_field_3": "text"},
            follow=True,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)

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

        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)
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

        response = self.client.post("/api/v2/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)
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
        response = self.client.get(
            f"/api/v2/events/1/registrations/{registration.pk}/", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)

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
            "/api/v2/events/1/registrations/",
            {
                "fields[info_field_1]": False,
                "fields[info_field_2": 42,
                "fields[info_field_3]": "text",
                "csrf": "random",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"]["pk"], self.member.pk)

        registration = EventRegistration.objects.get(
            event=self.event, member=self.member
        )
        self.assertEqual(field1.get_value_for(registration), None)
        self.assertEqual(field2.get_value_for(registration), None)
        self.assertEqual(field3.get_value_for(registration), None)

        response = self.client.patch(
            f"/api/v2/events/1/registrations/{registration.pk}/",
            {
                "fields[info_field_1]": True,
                "fields[info_field_2]": 1337,
                "fields[info_field_3]": "no text",
                "csrf": "random",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], self.member.pk)

        self.assertEqual(self.event.participants.count(), 1)
        registration = self.event.eventregistration_set.first()
        self.assertEqual(field1.get_value_for(registration), True)
        self.assertEqual(field2.get_value_for(registration), 1337)
        self.assertEqual(field3.get_value_for(registration), "no text")

    def test_registration_organiser(self):
        reg0 = EventRegistration.objects.create(event=self.event, member=self.member)
        reg1 = EventRegistration.objects.create(event=self.event, name="Test 1")
        reg2 = EventRegistration.objects.create(event=self.event, name="Test 2")

        self.member.is_superuser = True
        self.member.save()

        response = self.client.patch(
            f"/api/v2/events/1/registrations/{reg0.pk}/",
            {"csrf": "random", "present": True, "payment": "cash_payment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], self.member.pk)
        reg0.refresh_from_db()
        self.assertIsNotNone(reg0.payment_id)
        self.assertTrue(reg0.present)

        response = self.client.patch(
            f"/api/v2/registrations/{reg1.pk}/",
            {"csrf": "random", "present": True, "payment": "card_payment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], None)
        self.assertEqual(response.data["name"], "Test 1")
        reg1.refresh_from_db()
        self.assertEqual(reg1.payment.type, "card_payment")
        self.assertTrue(reg1.present)

        response = self.client.patch(
            f"/api/v2/registrations/{reg2.pk}/",
            {"csrf": "random", "present": False, "payment": "cash_payment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], None)
        self.assertEqual(response.data["name"], "Test 2")
        reg2.refresh_from_db()
        self.assertEqual(reg2.payment.type, "cash_payment")
        self.assertFalse(reg2.present)

    def test_mark_present_url_registered(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=1),
        )

        response = self.client.patch(self.mark_present_api_url, follow=True)
        self.assertContains(response, "You have been marked as present.")
        registration.refresh_from_db()
        self.assertTrue(registration.present)

    def test_mark_present_url_already_present(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=1),
            present=True,
        )

        response = self.client.patch(self.mark_present_api_url, follow=True)
        self.assertContains(response, "You were already marked as present.")
        registration.refresh_from_db()
        self.assertTrue(registration.present)

    def test_mark_present_url_not_registered(self):
        response = self.client.patch(self.mark_present_api_url, follow=True)
        self.assertContains(
            response, "You are not registered for this event.", status_code=403
        )

    def test_mark_present_url_wrong_token(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            member=self.member,
            date=timezone.now() - datetime.timedelta(hours=3),
        )
        response = self.client.patch(
            reverse(
                "api:v2:events:mark-present",
                kwargs={
                    "pk": self.event.pk,
                    "token": "11111111-2222-3333-4444-555555555555",
                },
            ),
            follow=True,
        )

        self.assertContains(response, "Invalid url.", status_code=403)
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
        response = self.client.patch(self.mark_present_api_url, follow=True)

        self.assertContains(response, "This event has already ended.", status_code=403)
        self.assertFalse(registration.present)


@override_settings(SUSPEND_SIGNALS=True)
class CalendarjsTest(TestCase):
    """Tests for CalendarJS/Fullcalendar view."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            title="testevent",
            description="desc",
            published=True,
            start=timezone.make_aware(datetime.datetime(2010, 1, 1, 20, 0, 0)),
            end=timezone.make_aware(datetime.datetime(2010, 1, 1, 22, 0, 0)),
            location="test location",
            map_location="test map location",
            price=13.37,
            fine=5.00,
        )
        cls.unpubEvent = Event.objects.create(
            pk=2,
            title="secretevent",
            description="desc",
            published=False,
            start=timezone.make_aware(datetime.datetime(2010, 1, 1, 20, 0, 0)),
            end=timezone.make_aware(datetime.datetime(2010, 1, 1, 22, 0, 0)),
            location="fake location",
            map_location="fake map location",
            price=6.66,
            fine=5.00,
        )
        cls.extEvent = ExternalEvent.objects.create(
            pk=3,
            organiser="Technicie",
            title="extevent",
            description="desc",
            published=True,
            start=timezone.make_aware(datetime.datetime(2010, 1, 1, 20, 0, 0)),
            end=timezone.make_aware(datetime.datetime(2010, 1, 1, 22, 0, 0)),
            location="partner location",
        )
        cls.event.organisers.add(Committee.objects.get(pk=1))
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_event_list(self):
        response = self.client.get(
            "/api/calendarjs/events/?start=2010-01-01T00%3A00%3A00%2B01%3A00&end=2011-01-01T00%3A00%3A00%2B01%3A00",
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "testevent")

    def test_unpub_event_list(self):
        response = self.client.get(
            "/api/calendarjs/events/unpublished/?start=2010-01-01T00%3A00%3A00%2B01%3A00&end=2011-01-01T00%3A00%3A00%2B01%3A00",
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "secretevent")

    def test_external_event_list(self):
        response = self.client.get(
            "/api/calendarjs/external/?start=2010-01-01T00%3A00%3A00%2B01%3A00&end=2011-01-01T00%3A00%3A00%2B01%3A00",
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "extevent (Technicie)")


@override_settings(SUSPEND_SIGNALS=True)
class EventApiV2Test(TestCase):
    """Tests for registration view."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            title="testevent",
            description="desc",
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=13.37,
            fine=5.00,
        )
        cls.event.organisers.add(Committee.objects.get(pk=1))
        cls.member = Member.objects.filter(last_name="Wiggers").first()

        cls.mark_present_api_url = reverse(
            "api:v2:events:mark-present",
            kwargs={
                "pk": cls.event.pk,
                "token": cls.event.mark_present_url_token,
            },
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_event_list(self):
        response = self.client.get("/api/v2/events/", format="json")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "testevent")
