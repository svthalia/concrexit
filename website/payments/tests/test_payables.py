from django.test import TestCase

from payments import payables, NotRegistered
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
