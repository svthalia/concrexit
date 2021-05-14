from unittest.mock import MagicMock

from django.db.models import Model

from payments import Payable


class MockModel:
    class Meta:
        app_label = "mock_app"
        model_name = "mock_model"

    payment = None
    pk = 1
    _meta = Meta()

    def __init__(
        self, payer, amount=5, topic="mock topic", notes="mock notes", payment=None
    ) -> None:
        self.payer = payer
        self.amount = amount
        self.topic = topic
        self.notes = notes
        self.payment = payment

        # Because we have to do as if this is a model sometimes
        self.verbose_name = "MockPayable"
        self.verbose_name_plural = self.verbose_name + "s"

    def save(self):
        pass


class MockPayable(Payable):
    save = MagicMock()

    @property
    def payment_amount(self):
        return self.model.amount

    @property
    def payment_topic(self):
        return self.model.topic

    @property
    def payment_notes(self):
        return self.model.notes

    @property
    def payment_payer(self):
        return self.model.payer

    def can_create_payment(self, member):
        return False
