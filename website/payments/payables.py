from functools import lru_cache

from django.db.models import Model
from django.db.models.signals import pre_save

from payments.exceptions import PaymentError

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

    @property
    def immutable_after_payment(self):
        return False

    def __hash__(self):
        return hash((self.payment_amount, self.payment_topic, self.payment_notes))


class Payables:
    _registry = {}

    @lru_cache(maxsize=None)
    def _get_key(self, model):
        return f"{model._meta.app_label}_{model._meta.model_name}"

    def get_payable(self, model: Model) -> Payable:
        if self._get_key(model) not in self._registry:
            raise NotRegistered(f"No Payable registered for {self._get_key(model)}")
        return self._registry[self._get_key(model)](model)

    def register(self, model: Model, payable_class: Payable):
        self._registry[self._get_key(model)] = payable_class
        pre_save.connect(prevent_saving_paid_after_immutable, sender=model)


payables = Payables()

def prevent_saving_paid_after_immutable(sender, instance, **kwargs):
    """Remove user from the order reminder when saved."""
    if not payables.get_payable(instance).immutable_after_payment:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    immutable_fields = ["payment_payer", "payment_amount", "payment_topic", "payment_notes"]

    if old_instance.payment and any(
        getattr(payables.get_payable(old_instance), x) != getattr(payables.get_payable(instance), x) for x in immutable_fields
    ): # THIS DOESNT WORK YET, AS THE OLD AND NEW PAYABLE ARE THE SAME
        raise PaymentError("Cannot change this model")
