import doctest

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from newsletters.models import Newsletter, NewsletterEvent
from newsletters.templatetags import listutil


def load_tests(loader, tests, ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in listutil
    tests.addTests(doctest.DocTestSuite(listutil))
    return tests


class NewslettersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jacob',
                                             email='jacob@test.com',
                                             password='top_secret',
                                             is_staff=True)

        self.user.user_permissions.set(
            Permission.objects.filter(content_type__app_label="newsletters")
        )

        self.user.backend = 'django.contrib.auth.backends.ModelBackend'
        self.user.save()

        self.client.force_login(self.user)

        self.testletter_sent = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=True)
        self.testletter_concept = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=False)

    def test_sent_change_redirect(self):
        response = self.client.get(reverse(
            'admin:newsletters_newsletter_change', args=[
                self.testletter_sent.pk]))
        self.assertRedirects(response, self.testletter_sent.get_absolute_url())

    def test_sent_confirm_redirect(self):
        response = self.client.get(reverse(
            'newsletters:admin-send', args=[self.testletter_sent.pk]))
        self.assertRedirects(response, self.testletter_sent.get_absolute_url())

    def test_concept_change_no_redirect(self):
        response = self.client.get(reverse(
            'admin:newsletters_newsletter_change',
            args=[self.testletter_concept.pk]))
        self.assertEqual(response.status_code, 200)

    def test_concept_confirm_no_redirect(self):
        response = self.client.get(reverse(
            'newsletters:admin-send', args=[self.testletter_concept.pk]))
        self.assertEqual(response.status_code, 200)

    def test_email_sent_per_lang(self):
        testletter = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=False)

        self.client.post(reverse(
            'newsletters:admin-send',
            args=[testletter.pk]), {'post': 'yes'})
        self.assertEqual(len(mail.outbox), len(settings.LANGUAGES))

    def test_email_html_and_text(self):
        testletter = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=False)

        self.client.post(reverse(
            'newsletters:admin-send',
            args=[testletter.pk]), {'post': 'yes'})

        for message in mail.outbox:
            # If body is present then it is text/plain by default
            self.assertTrue(message.body)
            self.assertEqual(message.alternatives[0][1],
                             'text/html')

    def test_email_sent_database_changed(self):
        testletter = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=False)

        self.client.post(reverse(
            'newsletters:admin-send',
            args=[testletter.pk]), {'post': 'yes'})

        testletter.refresh_from_db()

        self.assertTrue(testletter.sent)

    def test_email_sent_redirect(self):
        testletter = Newsletter.objects.create(
            title_nl='testletter',
            title_en='testletter',
            description_nl='testdesc',
            description_en='testdesc',
            sent=False)

        response = self.client.post(reverse(
            'newsletters:admin-send',
            args=[testletter.pk]), {'post': 'yes'})

        testletter.refresh_from_db()

        self.assertRedirects(response, reverse(
            'admin:newsletters_newsletter_changelist'))


class NewsletterEventsTest(TestCase):
    def test_until_date(self):
        m = NewsletterEvent(title_nl='testact',
                            title_en='testevent',
                            description_nl='testbesc',
                            description_en='testdesc',
                            what_nl='wat',
                            what_en='what',
                            where_nl='waar',
                            where_en='where',
                            start_datetime=timezone.now().date().replace(
                                year=2014, month=2, day=1),
                            end_datetime=timezone.now().date().replace(
                                year=2014, month=1, day=1))
        with self.assertRaises(ValidationError):
            m.clean()
        m.end_datetime = timezone.now().date().replace(
            year=2014, month=3, day=1)
        m.clean()
