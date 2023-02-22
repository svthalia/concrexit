from unittest import mock

from django.test import Client, TestCase, RequestFactory

from moneybird.webhooks.views import webhook_receive


class MoneybirdWebhooksViewsTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.client = Client()

    def _create_request(self, method, url, data=None, additional_headers=None):
        headers = {}
        if additional_headers:
            for key, value in additional_headers.items():
                headers[f"HTTP_{key}"] = value
        request = getattr(self.rf, method)(
            url, data, content_type="application/json", **headers
        )
        return request

    @mock.patch("moneybird.webhooks.views.process_webhook_payload")
    def test_webhook_receive(self, process_webhook_payload):
        data = {
            "webhook_id": "123",
            "webhook_token": "456",
            "administration_id": "789",
            "entity_type": "invoices",
        }
        request = self._create_request(
            "post",
            "/",
            data=data,
            additional_headers={"Idempotency-Key": "abc"},
        )

        with self.subTest("Successful request"):
            webhook_receive(request)
            process_webhook_payload.assert_called_once_with(data)

        process_webhook_payload.reset_mock()
        with self.subTest("Idempotency key already processed"):
            webhook_receive(request)
            process_webhook_payload.assert_not_called()

        process_webhook_payload.reset_mock()
        with self.subTest("No GET"):
            request = self._create_request("get", "/")
            webhook_receive(request)
            process_webhook_payload.assert_not_called()
