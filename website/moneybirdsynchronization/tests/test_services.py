from unittest import mock

from django.test import TestCase

from freezegun import freeze_time

from moneybirdsynchronization import services


class ServicesTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = cls.members.get(pk=1)
        cls.bank_account = cls.member.bank_accounts.first()

    @mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService.update_contact")
    @mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService.create_contact")
    def test_create_or_update_contact_with_mandate(
        self, mock_create_contact, mock_update_contact
    ):
        """Creating/updating a contact with a mandate excludes the mandate if it starts today.

        This is a limitation imposed by the Moneybird API.
        See: https://github.com/svthalia/concrexit/issues/3295.
        """
        # TODO: set mock response values:
        mock_create_contact.return_value = {}
        mock_update_contact.return_value = {}

        # Bank account is valid from 2016-07-07.
        with freeze_time("2016-07-07"):
            with self.subTest("Creating a contact does not push today's SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_create_contact.assert_called_once_with(
                    {},  # TODO: fill in the expected content, i.e. without the bank account.
                    # Possibly the mock return values need to be changed between the subtests.
                )

            with self.subTest("Updating a contact does not push today's SEPA mandate."):
                raise NotImplementedError

        with freeze_time("2016-07-08"):
            with self.subTest("Creating a contact pushes past SEPA mandate."):
                raise NotImplementedError

            with self.subTest("Updating a contact pushes past SEPA mandate."):
                raise NotImplementedError

    @mock.patch("moneybirdsynchronization.services.create_or_update_contact")
    def test_sync_contacts_with_outdated_mandates(self, mock_create_or_update_contact):
        # TODO: setup at least a contact with an outdated mandate, one with a correct mandate, and one with no mandate at all. Perhaps also one where moneybird has a mandate, but the user has invalidated it (so it is in fact outdated, and should be removed from moneybird).

        services.sync_contacts_with_outdated_mandates()

        # TODO: check that mock_create_or_update_contact was called with the right contacts.


# TODO: One more thing, of course one of the migrations can be removed.
