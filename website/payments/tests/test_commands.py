from unittest import mock

from django.test import TestCase, override_settings

from freezegun import freeze_time

from payments.management.commands.revokeoldmandates import Command


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class RevokeOldMandatesCommandTest(TestCase):
    """Test for the management command."""

    fixtures = ["members.json"]

    @mock.patch("payments.services.revoke_old_mandates")
    def test_handle(self, revoke_old_mandates):
        command = Command()
        command.handle()
        revoke_old_mandates.assert_called()
