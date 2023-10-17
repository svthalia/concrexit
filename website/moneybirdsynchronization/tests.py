from unittest import mock

from django.test import TestCase

from moneybirdsynchronization import services


class MoneybirdTest(TestCase):
    @mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService.update_contact")
    def test_moneybird_late_mandates(self, mandates_mock):
        services.send_mandates_late()
        mandates_mock.assert_called()
