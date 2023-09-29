from unittest.mock import patch

from django.test import TestCase

from registrations.tasks import minimise_registrations


class CeleryTest(TestCase):
    @patch("registrations.services.execute_data_minimisation")
    def test_minimise_registrations(self, mock_minimise_registrations):
        minimise_registrations()
        mock_minimise_registrations.assert_called_once()
