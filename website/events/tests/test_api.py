import datetime

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from activemembers.models import Committee
from events.models import (
    Event,
    EventRegistration,
    RegistrationInformationField,
    BooleanRegistrationInformation,
    IntegerRegistrationInformation,
    TextRegistrationInformation,
)
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class RegistrationApiTest(TestCase):
    """Tests for registration view."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            pk=1,
            organiser=Committee.objects.get(pk=1),
            title_en="testevent",
            description_en="desc",
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en="test location",
            map_location="test map location",
            price=13.37,
            fine=5.00,
        )
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_registration_register_not_required(self):
        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)
        self.assertEqual(self.event.participants.count(), 1)
        self.assertEqual(self.event.eventregistration_set.first().member, self.member)

    def test_registration_register_twice(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)
        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_closed(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_cancel(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()
        reg = EventRegistration.objects.create(event=self.event, member=self.member)
        response = self.client.delete(
            "/api/v1/registrations/{}/".format(reg.pk), follow=True
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
            name_en="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            required=False,
        )

        response = self.client.post(
            "/api/v1/events/1/registrations/",
            {"info_field_1": True, "info_field_2": 42, "info_field_3": "text"},
            follow=True,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)

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
            name_en="test bool",
            required=False,
        )

        RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            required=False,
        )

        RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            required=False,
        )

        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_fields_required(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.event.save()

        RegistrationInformationField.objects.create(
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test",
            required=True,
        )

        response = self.client.post("/api/v1/events/1/registrations/", follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)
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
            name_en="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
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
            "/api/v1/registrations/{}/".format(registration.pk), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], self.member.pk)

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
            name_en="test bool",
            required=False,
        )

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            required=False,
        )

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            required=False,
        )

        response = self.client.post(
            "/api/v1/events/1/registrations/",
            {
                "fields[info_field_1]": False,
                "fields[info_field_2": 42,
                "fields[info_field_3]": "text",
                "csrf": "random",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member"], self.member.pk)

        registration = EventRegistration.objects.get(
            event=self.event, member=self.member
        )
        self.assertEqual(field1.get_value_for(registration), None)
        self.assertEqual(field2.get_value_for(registration), None)
        self.assertEqual(field3.get_value_for(registration), None)

        response = self.client.patch(
            "/api/v1/registrations/{}/".format(registration.pk),
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
            "/api/v1/registrations/{}/".format(reg0.pk),
            {"csrf": "random", "present": True, "payment": "cash_payment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], self.member.pk)
        reg0.refresh_from_db()
        self.assertIsNotNone(reg0.payment_id)
        self.assertTrue(reg0.present)

        response = self.client.patch(
            "/api/v1/registrations/{}/".format(reg1.pk),
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
            "/api/v1/registrations/{}/".format(reg2.pk),
            {"csrf": "random", "present": False, "payment": "cash_payment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["member"], None)
        self.assertEqual(response.data["name"], "Test 2")
        reg2.refresh_from_db()
        self.assertEqual(reg2.payment.type, "cash_payment")
        self.assertFalse(reg2.present)
