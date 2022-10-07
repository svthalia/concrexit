from unittest import mock

from django.test import TestCase, override_settings

from payments.exceptions import PaymentError
from payments.templatetags.payments import payment_button
from payments.tests.__mocks__ import MockPayable


@override_settings(SUSPEND_SIGNALS=True)
class PaymentButtonTemplatetagTest(TestCase):
    """Tests the payment button templatetag."""

    def test_inserts_data(self):
        payable = MockPayable("test")
        payable.pk = 1

        with self.subTest("With payable and primary key"):
            with mock.patch(
                "django.contrib.contenttypes.models.ContentType.objects"
            ) as ct_objects:
                ct_objects.get_for_model.return_value.model = "model_name"
                ct_objects.get_for_model.return_value.app_label = "app_label"

                return_value = payment_button(payable, "https://next")
                self.assertEqual(
                    return_value,
                    {
                        "member": "test",
                        "pk": 1,
                        "model_name": "model_name",
                        "app_label": "app_label",
                        "redirect_to": "https://next",
                    },
                )

        with self.subTest("With payable and without primary key"):
            payable.pk = None
            with self.assertRaisesMessage(PaymentError, "Payable does not exist"):
                payment_button(payable, "https://next")
