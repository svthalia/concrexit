from functools import lru_cache

from django.db.models import Model

_registry = {}


class NotRegistered(Exception):
    pass


class Payable:
    def __init__(self, model: Model):
        self.model = model

    @property
    def pk(self):
        return self.model.pk

    @property
    def payment(self):
        return self.model.payment

    @payment.setter
    def payment(self, payment):
        self.model.payment = payment

    @property
    def payment_amount(self):
        raise NotImplementedError

    @property
    def payment_topic(self):
        raise NotImplementedError

    @property
    def payment_notes(self):
        raise NotImplementedError

    @property
    def payment_payer(self):
        raise NotImplementedError

    @property
    def tpay_allowed(self):
        return True

    def can_manage_payment(self, member):
        raise NotImplementedError


class Payables:
    _registry = {}

    def _get_key(self, model):
        return f"{model._meta.app_label}_{model._meta.model_name}"

    def get_payable(self, model: Model) -> Payable:
        if self._get_key(model) not in self._registry:
            raise NotRegistered(f"No Payable registered for {self._get_key(model)}")
        return self._registry[self._get_key(model)](model)

    def register(self, model: Model, payable_class: Payable):
        self._registry[self._get_key(model)] = payable_class


payables = Payables()
