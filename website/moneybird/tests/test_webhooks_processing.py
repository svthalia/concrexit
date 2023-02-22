from unittest import mock

from django.test import TestCase, override_settings

from moneybird.resource_types import MoneybirdResourceType
from moneybird.webhooks.events import WebhookEvent
from moneybird.webhooks.processing import process_webhook_payload


class MoneybirdWebhookProcessingTest(TestCase):
    @override_settings(MONEYBIRD_WEBHOOK_ID="987654321")
    @override_settings(MONEYBIRD_WEBHOOK_TOKEN="aBcDeFgHiJkLmNoPqRsTuVwXyZ")
    @override_settings(MONEYBIRD_ADMINISTRATION_ID=1234567890)
    @override_settings(MONEYBIRD_WEBHOOK_EVENTS=[WebhookEvent.SALES_INVOICE_CREATED])
    @mock.patch(
        "moneybird.resource_types.get_moneybird_resource_type_for_webhook_entity",
        return_value=MoneybirdResourceType,
    )
    @mock.patch("moneybird.resource_types.MoneybirdResourceType.process_webhook_event")
    def test_process_webhook_payload(self, process_webhook_event, _):
        data = {
            "administration_id": "1234567890",
            "webhook_id": "987654321",
            "webhook_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ",
            "entity_type": "SalesInvoice",
            "entity_id": "116015245643744263",
            "state": "new_state",
            "action": "sales_invoice_created",
            "entity": {"id": "116015245643744263", "data": "test"},
        }

        with self.subTest("Successful request"):
            process_webhook_payload(data)
            process_webhook_event.assert_called_once_with(
                data["entity"], WebhookEvent.SALES_INVOICE_CREATED
            )

        process_webhook_event.reset_mock()
        with self.subTest("Wrong webhook id"):
            data["webhook_id"] = "invalid"
            with self.assertRaises(ValueError):
                process_webhook_payload(data)
            process_webhook_event.assert_not_called()

        process_webhook_event.reset_mock()
        with self.subTest("Wrong webhook token"):
            data["webhook_id"] = "987654321"
            data["webhook_token"] = "invalid"
            with self.assertRaises(ValueError):
                process_webhook_payload(data)
            process_webhook_event.assert_not_called()

        process_webhook_event.reset_mock()
        with self.subTest("Wrong administration id"):
            data["webhook_token"] = "aBcDeFgHiJkLmNoPqRsTuVwXyZ"
            data["administration_id"] = "999999"
            with self.assertRaises(ValueError):
                process_webhook_payload(data)
            process_webhook_event.assert_not_called()

        process_webhook_event.reset_mock()
        with self.subTest("Wrong event"):
            data["administration_id"] = "1234567890"
            data["action"] = "sales_invoice_updated"
            with self.assertRaises(ValueError):
                process_webhook_payload(data)
            process_webhook_event.assert_not_called()

        process_webhook_event.reset_mock()
        with self.subTest("Invalid event"):
            data["action"] = "invalid"
            with self.assertRaises(ValueError):
                process_webhook_payload(data)
            process_webhook_event.assert_not_called()

        process_webhook_event.reset_mock()
        with mock.patch(
            "moneybird.resource_types.get_moneybird_resource_type_for_entity",
            return_value=None,
        ):
            with self.subTest("Unregistered resource type"):
                data["action"] = "sales_invoice_created"
                data["entity_type"] = "invalid"
                with self.assertRaises(ValueError):
                    process_webhook_payload(data)
                process_webhook_event.assert_not_called()
