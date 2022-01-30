"""Defines tests for the newsletters package."""
import doctest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from members.models import Membership, Profile
from newsletters.models import Newsletter, NewsletterEvent
from newsletters.templatetags import listutil


def load_tests(loader, tests, ignore):
    """Load all tests in this module."""
    # Adds the doctests in listutil
    tests.addTests(doctest.DocTestSuite(listutil))
    return tests


@override_settings(SUSPEND_SIGNALS=True)
class NewslettersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="jacob",
            email="jacob@test.com",
            password="top_secret",
            is_staff=True,
        )
        Profile.objects.create(
            user=cls.user,
            address_street="street",
            address_postal_code="1234AB",
            address_city="city",
        )
        Membership.objects.create(
            type=Membership.MEMBER, user=cls.user, since=timezone.now()
        )

        cls.user2 = get_user_model().objects.create_user(
            username="janwillem",
            email="janwillem@test.com",
            password="top_secret",
            is_staff=False,
        )
        Profile.objects.create(
            user=cls.user2,
            address_street="street",
            address_postal_code="1234AB",
            address_city="city",
        )
        Membership.objects.create(
            type=Membership.MEMBER, user=cls.user2, since=timezone.now()
        )

        cls.user3 = get_user_model().objects.create_user(
            username="thijs",
            email="thijs@test.com",
            password="top_secret",
            is_staff=False,
        )
        Profile.objects.create(
            user=cls.user3,
            address_street="street",
            address_postal_code="1234AB",
            address_city="city",
        )
        Membership.objects.create(
            type=Membership.MEMBER, user=cls.user3, since=timezone.now()
        )

        cls.user.user_permissions.set(
            Permission.objects.filter(content_type__app_label="newsletters")
        )

        cls.user.backend = "django.contrib.auth.backends.ModelBackend"
        cls.user.save()

        cls.testletter_sent = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=True,
        )
        cls.testletter_concept = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_sent_change_redirect(self):
        response = self.client.get(
            reverse(
                "admin:newsletters_newsletter_change", args=[self.testletter_sent.pk]
            )
        )
        self.assertRedirects(response, self.testletter_sent.get_absolute_url())

    def test_sent_confirm_redirect(self):
        response = self.client.get(
            reverse("newsletters:admin-send", args=[self.testletter_sent.pk])
        )
        self.assertRedirects(response, self.testletter_sent.get_absolute_url())

    def test_concept_change_no_redirect(self):
        response = self.client.get(
            reverse(
                "admin:newsletters_newsletter_change", args=[self.testletter_concept.pk]
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_concept_confirm_no_redirect(self):
        response = self.client.get(
            reverse("newsletters:admin-send", args=[self.testletter_concept.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_email_sent_per_lang(self):
        testletter = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

        self.client.post(
            reverse("newsletters:admin-send", args=[testletter.pk]), {"post": "yes"}
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_email_html_and_text(self):
        testletter = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

        self.client.post(
            reverse("newsletters:admin-send", args=[testletter.pk]), {"post": "yes"}
        )

        for message in mail.outbox:
            # If body is present then it is text/plain by default
            self.assertTrue(message.body)
            self.assertEqual(message.alternatives[0][1], "text/html")

    def test_email_sent_database_changed(self):
        testletter = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

        self.client.post(
            reverse("newsletters:admin-send", args=[testletter.pk]), {"post": "yes"}
        )

        testletter.refresh_from_db()

        self.assertTrue(testletter.sent)

    def test_email_sent_redirect(self):
        testletter = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

        response = self.client.post(
            reverse("newsletters:admin-send", args=[testletter.pk]), {"post": "yes"}
        )

        testletter.refresh_from_db()

        self.assertRedirects(
            response, reverse("admin:newsletters_newsletter_changelist")
        )


class NewsletterEventsTest(TestCase):
    def test_until_date(self):
        m = NewsletterEvent(
            title="testevent",
            description="testdesc",
            where="where",
            start_datetime=timezone.now().date().replace(year=2014, month=2, day=1),
            end_datetime=timezone.now().date().replace(year=2014, month=1, day=1),
        )
        with self.assertRaises(ValidationError):
            m.clean()
        m.end_datetime = timezone.now().date().replace(year=2014, month=3, day=1)
        m.clean()
