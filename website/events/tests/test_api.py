import datetime

from activemembers.models import Committee
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from events.models import Event, EventRegistration
from events.models.external_event import ExternalEvent
from members.models import Member
from rest_framework.test import APIClient


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

    def test_event_detail(self):
        response = self.client.get("/api/v2/events/1/", format="json")
        self.assertEqual(response.data["title"], "testevent")

    def test_event_detail_not_found(self):
        response = self.client.get("/api/v2/events/2/", format="json")
        self.assertEqual(response.status_code, 404)

    def test_event_detail_unpublished(self):
        self.event.published = False
        self.event.save()
        response = self.client.get("/api/v2/events/1/", format="json")
        self.assertEqual(response.status_code, 404)
