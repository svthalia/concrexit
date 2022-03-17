from unittest.mock import MagicMock, patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from payments import (
    payables,
    NotRegistered,
    prevent_saving,
    PaymentError,
    Payable,
    prevent_saving_related,
)
from payments.models import Payment
from payments.tests.__mocks__ import MockModel, MockPayable


class PayablesTest(TestCase):
    def setUp(self):
        payables.register(MockModel, MockPayable)

    def test_registered_payable(self):
        self.assertIsInstance(payables.get_payable(MockModel), MockPayable)

    def test_not_registered_payable(self):
        payables._registry = {}
        with self.assertRaises(NotRegistered):
            payables.get_payable(MockModel)


class ImmutablePayablesTest(TestCase):
    def setUp(self):
        payables.register(MockModel, MockPayable)

    def test_register(self):
        with self.subTest("Register not immutable"):
            MockPayable.immutable_after_payment = False
            payables.register(MockModel, MockPayable)

        with self.subTest("Register immutable"):
            MockPayable.immutable_after_payment = True
            MockPayable.immutable_model_fields_after_payment = [
                "test_field",
            ]
            payables.register(MockModel, MockPayable)

    def test_prevent_unlinking_payment_from_payable(self):
        model_before = MockModel(payer=None)
        model_after = MockModel(payer=None)
        model_before.payment = Payment.objects.create(
            type=Payment.CARD, amount=2, notes="test payment", topic="test topic"
        )
        MockPayable.immutable_after_payment = True
        MockPayable.immutable_model_fields_after_payment = [
            "test_field",
        ]
        MockPayable.get_payment = MagicMock(return_value=model_before.payment)
        MockModel.objects.get = MagicMock(return_value=model_before)

        with self.subTest("Unlinking a payment"):
            model_after.payment = None
            self.assertRaises(PaymentError, prevent_saving, MockModel, model_after)

        with self.subTest("Changing an immutable model field after payment"):
            model_after.payment = model_before.payment
            model_after.test_field = "changed"
            self.assertRaises(PaymentError, prevent_saving, MockModel, model_after)

    def test_prevent_saving_no_existing_model(self):
        model = MockModel(payer=None)
        model.pk = None
        prevent_saving(MockModel, model)  # this should not crash

    def test_prevent_saving_not_immutable(self):
        MockPayable.immutable_after_payment = False
        model = MockModel(payer=None)
        model.pk = 1
        prevent_saving(MockModel, model)  # this should not crash

    def test_prevent_saving_model_with_pk_but_not_in_db(self):
        MockPayable.immutable_after_payment = True
        model = MockModel(payer=None)
        model.payment = Payment.objects.create(
            type=Payment.CARD, amount=2, notes="test payment", topic="test topic"
        )
        MockPayable.get_payment = MagicMock(return_value=model.payment)
        MockModel.DoesNotExist = ObjectDoesNotExist
        MockModel.objects.get = MagicMock(side_effect=MockModel.DoesNotExist)
        model.pk = 1
        prevent_saving(MockModel, model)  # this should not crash

    def test_allow_adding_a_payment_to_unpaid_model(self):
        MockPayable.immutable_after_payment = True
        model_before = MockModel(payer=None)
        model_before.payment = None

        model_after = MockModel(payer=None)
        model_after.payment = Payment.objects.create(
            type=Payment.CARD, amount=2, notes="test payment", topic="test topic"
        )

        MockModel.objects.get = MagicMock(return_value=model_before)
        prevent_saving(MockModel, model_after)

    def test_mutable_model(self):
        payable = payables.get_payable(MockModel)
        MockPayable.immutable_after_payment = False
        self.assertFalse(payable.immutable_after_payment)
        MockPayable.immutable_after_payment = True
        self.assertTrue(payable.immutable_after_payment)

        self.assertFalse(Payable.immutable_after_payment)

    def test_immutable_fields(self):
        payable = payables.get_payable(MockModel)
        MockPayable.immutable_model_fields_after_payment = ["test1", "test2"]
        self.assertEqual(
            ["test1", "test2"], payable.immutable_model_fields_after_payment
        )
        MockPayable.immutable_model_fields_after_payment = []
        self.assertEqual([], payable.immutable_model_fields_after_payment)

        self.assertEqual([], Payable.immutable_model_fields_after_payment)

    def test_prevent_saving_changed_related_model_field(self):
        MockModel2 = MockModel
        MockPayable.immutable_after_payment = True
        MockPayable.immutable_model_fields_after_payment = {MockModel2: ["test_field"]}
        model = MockModel(payer=None)
        model.payment = Payment.objects.create(
            type=Payment.CARD, amount=2, notes="test payment", topic="test topic"
        )

        related_model_before = MockModel2(payer=None)
        related_model_before.test_related_field = model
        related_model_before.test_field = "test"

        related_model_after = MockModel2(payer=None)
        related_model_after.test_related_field = model
        related_model_after.test_field = "changed"

        MockPayable.immutable_after_payment = True
        MockPayable.immutable_foreign_key_models = {MockModel2: ["test_related_field"]}

        with self.subTest("Prevent saving changed field in related model"):
            MockModel2.objects.get = MagicMock(return_value=related_model_before)
            self.assertRaises(
                PaymentError,
                prevent_saving_related("test_related_field"),
                MockModel2,
                related_model_after,
            )

        with self.subTest("Do nothing if field is not changed related model"):
            MockModel2.objects.get = MagicMock(return_value=related_model_before)
            related_model_after.test_field = "test"
            prevent_saving_related("test_related_field")(
                MockModel2, related_model_after
            )

        with self.subTest("Do nothing if parent is not immutable"):
            MockPayable.immutable_after_payment = False
            prevent_saving_related("test_related_field")(
                MockModel2, related_model_after
            )

        with self.subTest(
            "Do nothing if related model changed fields are not labelled immutable"
        ):
            MockPayable.immutable_after_payment = True
            MockPayable.immutable_model_fields_after_payment = {MockModel2: []}
            prevent_saving_related("test_related_field")(
                MockModel2, related_model_after
            )

        with self.subTest("Error if model does not exist"):
            MockPayable.immutable_after_payment = True
            MockPayable.immutable_foreign_key_models = {
                MockModel2: ["test_related_field"]
            }
            MockModel2.DoesNotExist = ObjectDoesNotExist
            MockModel2.objects.get = MagicMock(side_effect=MockModel2.DoesNotExist)
            self.assertRaises(
                PaymentError,
                prevent_saving_related("test_related_field"),
                MockModel2,
                related_model_after,
            )
