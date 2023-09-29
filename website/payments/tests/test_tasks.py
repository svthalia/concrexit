from unittest.mock import patch

from django.test import TestCase

from payments.tasks import revoke_mandates


class CeleryTest(TestCase):
    @patch("payments.services.revoke_old_mandates")
    def test_minimise_registrations(self, mock_revoke_mandates):
        revoke_mandates()
        mock_revoke_mandates.assert_called_once()
