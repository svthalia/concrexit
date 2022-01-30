import uuid
from unittest import mock

from django.conf import settings
from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from members.models import Member, Profile
from registrations import emails
from utils.snippets import send_email
from registrations.models import Registration, Renewal


class EmailsTest(TestCase):
    def setUp(self):
        translation.activate("en")

    @mock.patch("registrations.emails.send_email")
    def test_send_registration_email_confirmation(self, send_email):
        reg = Registration(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            pk=uuid.uuid4(),
        )

        emails.send_registration_email_confirmation(reg)

        send_email.assert_called_once_with(
            reg.email,
            _("Confirm email address"),
            "registrations/email/registration_confirm_mail.txt",
            {
                "name": reg.get_full_name(),
                "confirm_link": (
                    "https://thalia.localhost"
                    + reverse("registrations:confirm-email", args=[reg.pk])
                ),
            },
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_registration_accepted_message(self, send_email):
        reg = Registration(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            pk=0,
            contribution=2,
        )

        emails.send_registration_accepted_message(reg)

        send_email.assert_called_once_with(
            reg.email,
            _("Registration accepted"),
            "registrations/email/registration_accepted.txt",
            {"name": reg.get_full_name(), "fees": floatformat(reg.contribution, 2)},
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_registration_rejected_message(self, send_email):
        reg = Registration(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            pk=0,
        )

        emails.send_registration_rejected_message(reg)

        send_email.assert_called_once_with(
            reg.email,
            _("Registration rejected"),
            "registrations/email/registration_rejected.txt",
            {"name": reg.get_full_name()},
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_new_registration_board_message(self, send_email):
        registration = Registration(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            pk=0,
        )

        emails.send_new_registration_board_message(registration)

        send_email.assert_called_once_with(
            settings.BOARD_NOTIFICATION_ADDRESS,
            "New registration",
            "registrations/email/registration_board.txt",
            {
                "name": registration.get_full_name(),
                "url": (
                    "https://thalia.localhost"
                    + reverse(
                        "admin:registrations_registration_change",
                        args=[registration.pk],
                    )
                ),
            },
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_renewal_accepted_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            profile=Profile(),
        )

        renewal = Renewal(pk=0, member=member, contribution=2)

        emails.send_renewal_accepted_message(renewal)

        send_email.assert_called_once_with(
            renewal.member.email,
            _("Renewal accepted"),
            "registrations/email/renewal_accepted.txt",
            {
                "name": renewal.member.get_full_name(),
                "fees": floatformat(renewal.contribution, 2),
                "thalia_pay_enabled": settings.THALIA_PAY_ENABLED_PAYMENT_METHOD,
                "url": (
                    settings.BASE_URL
                    + reverse(
                        "registrations:renew",
                    )
                ),
            },
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_renewal_rejected_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            profile=Profile(),
        )

        renewal = Renewal(pk=0, member=member)

        emails.send_renewal_rejected_message(renewal)

        send_email.assert_called_once_with(
            renewal.member.email,
            _("Renewal rejected"),
            "registrations/email/renewal_rejected.txt",
            {"name": renewal.member.get_full_name()},
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_renewal_complete_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            profile=Profile(),
        )

        renewal = Renewal(pk=0, member=member)

        emails.send_renewal_complete_message(renewal)

        send_email.assert_called_once_with(
            renewal.member.email,
            _("Renewal successful"),
            "registrations/email/renewal_complete.txt",
            {"name": renewal.member.get_full_name()},
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_new_renewal_board_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            profile=Profile(),
        )

        renewal = Renewal(pk=0, member=member)

        emails.send_new_renewal_board_message(renewal)

        send_email.assert_called_once_with(
            settings.BOARD_NOTIFICATION_ADDRESS,
            "New renewal",
            "registrations/email/renewal_board.txt",
            {
                "name": renewal.member.get_full_name(),
                "url": (
                    "https://thalia.localhost"
                    + reverse("admin:registrations_renewal_change", args=[renewal.pk])
                ),
            },
        )

    @mock.patch("registrations.emails.send_email")
    def test_send_references_information_message(self, send_email):
        with self.subTest("Registrations"):
            registration = Registration(
                email="test@example.org",
                first_name="John",
                last_name="Doe",
                pk=uuid.uuid4(),
            )

            emails.send_references_information_message(registration)

            send_email.assert_called_once_with(
                "test@example.org",
                "Information about references",
                "registrations/email/references_information.txt",
                {
                    "name": registration.get_full_name(),
                    "reference_link": (
                        "https://thalia.localhost"
                        + reverse("registrations:reference", args=[registration.pk])
                    ),
                },
            )

        send_email.reset_mock()

        with self.subTest("Renewals"):
            member = Member(
                email="test@example.org",
                first_name="John",
                last_name="Doe",
                profile=Profile(),
            )

            renewal = Renewal(pk=uuid.uuid4(), member=member)

            emails.send_references_information_message(renewal)

            send_email.assert_called_once_with(
                "test@example.org",
                "Information about references",
                "registrations/email/references_information.txt",
                {
                    "name": renewal.member.get_full_name(),
                    "reference_link": (
                        "https://thalia.localhost"
                        + reverse("registrations:reference", args=[renewal.pk])
                    ),
                },
            )

    def test_send_email(self):
        send_email(
            subject="Subject",
            to="test@example.org",
            body_template="registrations/email/renewal_board.txt",
            context={
                "name": "name",
                "url": "",
            },
        )

        self.assertEqual(mail.outbox[0].subject, "[THALIA] Subject")
        self.assertEqual(mail.outbox[0].to, ["test@example.org"])
        self.assertEqual(
            mail.outbox[0].body,
            loader.render_to_string(
                "registrations/email/renewal_board.txt",
                {
                    "name": "name",
                    "url": "",
                },
            ),
        )
