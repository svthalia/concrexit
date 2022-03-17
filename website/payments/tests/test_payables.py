from unittest.mock import MagicMock

from django.test import TestCase

from payments import payables, NotRegistered, prevent_saving, PaymentError, \
    Payable
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

    def test_prevent_unlinking_payment_from_payable(self):
        model_before = MockModel(payer=None)
        model_after = MockModel(payer=None)
        model_before.payment = Payment.objects.create(
            type=Payment.CARD, amount=2, notes="test payment", topic="test topic"
        )
        MockPayable.get_payment = MagicMock(return_value=model_before.payment)
        MockModel.objects.get = MagicMock(return_value=model_before)

        with self.subTest("Unlinking a payment"):
            model_after.payment = None

            with self.assertRaises(PaymentError) as test:
                prevent_saving(MockModel, model_after)

            exception = test.exception
            self.assertEqual(
                str(exception), "You are trying to unlink a payment from its payable."
            )

        with self.subTest("Changing an immutable model field after payment"):
            model_after.payment = model_before.payment
            model_after.test_field = "changed"

            with self.assertRaises(PaymentError) as test:
                prevent_saving(MockModel, model_after)

            exception = test.exception
            self.assertEqual(str(exception), "Cannot change this model")


    def test_prevent_saving_no_existing_model(self):
        model = MockModel(payer=None)
        model.pk = None
        prevent_saving(MockModel, model) # this should not crash


    def test_allow_adding_a_payment_to_unpaid_model(self):
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
        self.assertTrue(payable.immutable_after_payment)
        MockPayable.immutable_after_payment = False
        self.assertFalse(payable.immutable_after_payment)
        MockPayable.immutable_after_payment = True
        self.assertTrue(payable.immutable_after_payment)

        self.assertFalse(Payable.immutable_after_payment)

    def test_immutable_fields(self):
        payable = payables.get_payable(MockModel)
        self.assertEqual(["test_field"], payable.immutable_model_fields_after_payment)
        MockPayable.immutable_model_fields_after_payment = ["test1", "test2"]
        self.assertEqual(
            ["test1", "test2"], payable.immutable_model_fields_after_payment
        )
        MockPayable.immutable_model_fields_after_payment = []
        self.assertEqual([], payable.immutable_model_fields_after_payment)

        self.assertEqual([], Payable.immutable_model_fields_after_payment)




# def test_allow_saving_payable_without_immutable_field(self):
#     pass
#     # subtest: no payment
#     # subtest: unsaved payment
#     # subtest: with payment
