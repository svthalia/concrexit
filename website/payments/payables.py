from functools import lru_cache

from django.db.models import Model
from django.db.models.signals import pre_save
from django.utils.functional import classproperty

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

    def get_payment(self):
        if self.model.pk:
            self.model.refresh_from_db(fields=["payment"])
        return self.payment

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

    @classproperty
    def immutable_after_payment(self):
        return False

    @classproperty
    def immutable_foreign_key_models(self):
        return {}

    @classproperty
    def immutable_model_fields_after_payment(self):
        return []

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
        if payable_class.immutable_after_payment:
            pre_save.connect(prevent_saving, sender=model)

            for foreign_model in payable_class.immutable_foreign_key_models:
                foreign_key_field = payable_class.immutable_foreign_key_models[
                    foreign_model
                ]
                pre_save.connect(
                    prevent_saving_related(foreign_key_field), sender=foreign_model
                )


payables = Payables()


def prevent_saving(sender, instance, **kwargs):
    if not instance.pk:
        # Do nothing if the model is not created yet
        return

    payable = payables.get_payable(instance)
    if not payable.immutable_after_payment:
        # Do nothing if the model is not marked as immutable
        return
    if not payable.payment:
        # Do nothing if the model is not actually paid
        if payable.get_payment() is not None:
            # If this happens, there was a payment, but it is being deleted
            raise PaymentError("You are trying to unlink a payment from its payable.")
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    immutable_fields = (
        payable.immutable_model_fields_after_payment[sender]
        if isinstance(payable.immutable_model_fields_after_payment, dict)
        else payable.immutable_model_fields_after_payment
    )
    for field in immutable_fields:
        if getattr(old_instance, field) != getattr(instance, field):
            raise PaymentError("Cannot change this model")


def prevent_saving_related(foreign_key_field):
    def prevent_related_saving_paid_after_immutable(sender, instance, **kwargs):
        nonlocal foreign_key_field
        payable = payables.get_payable(getattr(instance, foreign_key_field))
        if not payable.immutable_after_payment:
            # Do nothing if the parent is not marked as immutable
            return
        if not payable.payment:
            # Do nothing if the parent is not actually paid
            return
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            raise PaymentError(  # pylint: disable=W0707
                "Cannot save this model with foreign key to immutable payment"
            )

        immutable_fields = (
            payable.immutable_model_fields_after_payment[sender]
            if isinstance(payable.immutable_model_fields_after_payment, dict)
            else []
        )
        for field in immutable_fields:
            if getattr(old_instance, field) != getattr(instance, field):
                raise PaymentError("Cannot change this model")

    return prevent_related_saving_paid_after_immutable
