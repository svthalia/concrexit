from datetime import datetime
from unittest.mock import MagicMock

from django.test import TestCase

from members.models import Membership
from registrations.payables import EntryPayable, RegistrationPayable, RenewalPayable


class EntryPayableTest(TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.model.contribution = 2
        self.model.membership = MagicMock()
        self.model.membership.user = "user"
        self.model.created_at = datetime(2018, 3, 4, 12, 0, 0)
        self.model.updated_at = datetime(2018, 3, 5, 12, 0, 0)

        self.payable = EntryPayable(self.model)

    def test_attributes(self):
        self.assertEqual(self.payable.payment_amount, 2)
        self.assertEqual(self.payable.payment_payer, "user")
        self.payable.model.membership = None
        self.assertEqual(self.payable.payment_payer, None)
        self.assertEqual(self.payable.payment_topic, "Registration entry")
        self.assertEqual(
            self.payable.payment_notes,
            "Registration entry. Creation date: March 4, 2018. Completion date: March 5, 2018",
        )
        self.assertFalse(self.payable.can_create_payment(None))


class RegistrationPayableTest(TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.model.contribution = 2
        self.model.membership = MagicMock()
        self.model.membership.user = "user"
        self.model.length = "1 year"
        self.model.membership_type = Membership.BENEFACTOR
        self.model.created_at = datetime(2018, 3, 4, 12, 0, 0)
        self.model.updated_at = datetime(2018, 3, 5, 12, 0, 0)

        self.payable = RegistrationPayable(self.model)

    def test_attributes(self):
        self.assertEqual(
            self.payable.payment_topic, "Membership registration benefactor (1 year)"
        )


class RenewalPayableTest(TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.model.contribution = 2
        self.model.membership = MagicMock()
        self.model.member = "member"
        self.model.length = "1 year"
        self.model.membership_type = Membership.BENEFACTOR
        self.model.created_at = datetime(2018, 3, 4, 12, 0, 0)
        self.model.updated_at = datetime(2018, 3, 5, 12, 0, 0)

        self.payable = RenewalPayable(self.model)

    def test_attributes(self):
        self.assertEqual(self.payable.payment_payer, "member")
        self.assertEqual(
            self.payable.payment_topic, "Membership renewal benefactor (1 year)"
        )
