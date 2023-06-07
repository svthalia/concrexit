from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase

from registrations.management.commands.minimiseregistrations import Command


class ManagementMinimiseTest(TestCase):
    def test_add_argument(self):
        mock_parser = MagicMock()
        Command().add_arguments(mock_parser)
        mock_parser.add_argument.assert_called_with(
            "--dry-run",
            action="store_true",
            default=False,
            dest="dry-run",
            help="Dry run instead of saving data",
        )

    @mock.patch("registrations.services.execute_data_minimisation")
    def test_handle(self, execute_data_minimisation):
        Command().handle({}, **{"dry-run": False})
        execute_data_minimisation.assert_called_with(False)
        Command().handle({}, **{"dry-run": True})
        execute_data_minimisation.assert_called_with(True)
