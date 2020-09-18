from unittest.mock import MagicMock

from payments.models import Payable


class MockPayable(Payable):
    save = MagicMock()

    def __init__(
        self, payer, amount=5, topic="mock topic", notes="mock notes", payment=None
    ) -> None:
        super().__init__()
        self.payer = payer
        self.amount = amount
        self.topic = topic
        self.notes = notes
        self.payment = payment

        # Because we have to do as if this is a model sometimes
        self.verbose_name = "MockPayable"
        self.verbose_name_plural = self.verbose_name + "s"
        self.pk = 0

    @property
    def payment_amount(self):
        return self.amount

    @property
    def payment_topic(self):
        return self.topic

    @property
    def payment_notes(self):
        return self.notes

    @property
    def payment_payer(self):
        return self.payer
