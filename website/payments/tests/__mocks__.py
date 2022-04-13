from unittest.mock import MagicMock

from django.utils.functional import classproperty

from payments import Payable


class MockManager:
    pass


class MockModel:
    class Meta:
        app_label = "mock_app"
        model_name = "mock_model"

    payment = None
    pk = 1
    test_field = ""
    _meta = Meta()
    objects = MockManager()

    def __init__(
        self,
        payer,
        amount=5,
        topic="mock topic",
        notes="mock notes",
        payment=None,
        can_manage=True,
    ) -> None:
        self.payer = payer
        self.amount = amount
        self.topic = topic
        self.notes = notes
        self.payment = payment
        self.can_manage = can_manage

        # Because we have to do as if this is a model sometimes
        self.verbose_name = "MockPayable"
        self.verbose_name_plural = self.verbose_name + "s"

    def save(self):
        pass

    def refresh_from_db(self):
        pass


class MockPayable(Payable):
    save = MagicMock()
    verbose_name = "MockPayable"
    verbose_name_plural = "MockPayables"

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

    def can_manage_payment(self, member):
        return self.model.can_manage

    @classproperty
    def immutable_after_payment(self):
        return False

    @classproperty
    def immutable_foreign_key_models(self):
        return {}

    @classproperty
    def immutable_model_fields_after_payment(self):
        return []
