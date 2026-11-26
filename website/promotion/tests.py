from datetime import date, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APIClient

from events.models import Event
from members.models import Member
from promotion.models import PromotionChannel, PromotionRequest


class PromotionRequestListTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Versteeg").first()
        cls.url = reverse("api:v2:promotion:promotion-requests")
        cls.application = Application.objects.create(
            name="Promo",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        channel = PromotionChannel.objects.create(name="WhatsApp")
        event = Event.objects.create(
            title="Borrel",
            description="desc",
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
            location="here",
            map_location="here",
            price=0,
            fine=0,
        )
        cls.with_event = PromotionRequest.objects.create(
            event=event,
            publish_date=date(2026, 12, 1),
            channel=channel,
            assigned_to="Someone",
            remarks="<p>Use the <b>blue</b> poster</p>",
        )
        cls.without_event = PromotionRequest.objects.create(
            publish_date=date(2026, 11, 20), channel=channel
        )

    def setUp(self):
        self.client = APIClient()

    def _authenticate(self, scope, permitted=True):
        if permitted:
            self.member.user_permissions.add(
                Permission.objects.get(codename="use_promotion_tools")
            )
        token = AccessToken.objects.create(
            user=self.member,
            application=self.application,
            token="token",
            scope=scope,
            expires=timezone.now() + timedelta(hours=1),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.token}")

    def test_lists_requests_by_publish_date(self):
        self._authenticate("promotion:read")
        results = self.client.get(self.url).json()["results"]
        self.assertEqual(
            [r["pk"] for r in results], [self.without_event.pk, self.with_event.pk]
        )
        self.assertEqual(
            results[1],
            {
                "pk": self.with_event.pk,
                "event": self.with_event.event.pk,
                "event_title": "Borrel",
                "event_start": self.with_event.event.start.astimezone().isoformat(),
                "event_url": "http://testserver"
                + self.with_event.event.get_absolute_url(),
                "event_description": "desc",
                "publish_date": "2026-12-01",
                "channel": "WhatsApp",
                "status": "not_started",
                "assigned_to": "Someone",
                "drive_folder": None,
                "remarks": "<p>Use the <b>blue</b> poster</p>",
            },
        )
        self.assertIsNone(results[0]["event_title"])

    def test_filters_on_publish_date(self):
        self._authenticate("promotion:read")
        response = self.client.get(
            self.url, {"start": "2026-11-21", "end": "2026-12-01"}
        )
        self.assertEqual(
            [r["pk"] for r in response.json()["results"]], [self.with_event.pk]
        )
        self.assertEqual(self.client.get(self.url, {"start": "nope"}).status_code, 400)

    def test_without_permission(self):
        self._authenticate("promotion:read", permitted=False)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_without_scope(self):
        self._authenticate("read")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_update_status(self):
        self._authenticate("promotion:write")
        url = reverse(
            "api:v2:promotion:promotion-request", args=[self.without_event.pk]
        )
        response = self.client.patch(url, {"status": "published"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "published")
        self.without_event.refresh_from_db()
        self.assertEqual(self.without_event.status, "published")

    def test_retrieve_request(self):
        self._authenticate("promotion:read")
        url = reverse("api:v2:promotion:promotion-request", args=[self.with_event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pk"], self.with_event.pk)

    def test_update_only_changes_status(self):
        self._authenticate("promotion:write")
        url = reverse("api:v2:promotion:promotion-request", args=[self.with_event.pk])
        self.client.patch(
            url, {"status": "started", "assigned_to": "Mallory"}, format="json"
        )
        self.with_event.refresh_from_db()
        self.assertEqual(
            (self.with_event.status, self.with_event.assigned_to),
            ("started", "Someone"),
        )
        bad = self.client.patch(url, {"status": "nonsense"}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_update_needs_write_scope(self):
        self._authenticate("promotion:read")
        url = reverse("api:v2:promotion:promotion-request", args=[self.with_event.pk])
        response = self.client.patch(url, {"status": "published"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_filters_on_status(self):
        self.without_event.status = "published"
        self.without_event.save()
        self._authenticate("promotion:read")
        response = self.client.get(self.url, {"status": "not_started,started,finished"})
        self.assertEqual(
            [r["pk"] for r in response.json()["results"]], [self.with_event.pk]
        )
        self.assertEqual(self.client.get(self.url, {"status": "nope"}).status_code, 400)

    def _authenticate_as_application(self, owner):
        """Use a client credentials token (no user) of an application owned by `owner`."""
        application = Application.objects.create(
            name="Promo tool",
            user=owner,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        token = AccessToken.objects.create(
            user=None,
            application=application,
            token=f"app-token-{owner and owner.pk}",
            scope="promotion:read promotion:write",
            expires=timezone.now() + timedelta(hours=1),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.token}")

    def test_application_token_acts_as_its_owner(self):
        self.member.user_permissions.add(
            Permission.objects.get(codename="use_promotion_tools")
        )
        self._authenticate_as_application(self.member)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        url = reverse("api:v2:promotion:promotion-request", args=[self.with_event.pk])
        response = self.client.patch(url, {"status": "published"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_application_token_without_permitted_owner(self):
        self._authenticate_as_application(self.member)  # owner lacks the permission
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self._authenticate_as_application(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)
