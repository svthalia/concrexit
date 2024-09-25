from abc import ABC, abstractmethod
from decimal import Decimal
from functools import lru_cache
from typing import Generic, TypeVar

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models.signals import pre_save
from django.utils.functional import classproperty

from members.models.member import Member
from payments.exceptions import PaymentError

PayableModel = TypeVar("PayableModel", bound=Model)


class NotRegistered(Exception):
    pass


class Payable(ABC, Generic[PayableModel]):
    """Base class for a wrapper around a model that can be paid for.

    This class provides a common interface for different models for which
    a payment can be made. For each payable model, a subclass of `Payable`
    should be created that implements the necessary properties and methods.

    These `Payable` wrapper classes are then registered in the global `payables`
    registry, which handles logic for preventing disallowed changes to paid model
    instances, and provides a factory for the `Payable` objects from model instances.

    For type hinting, an implementation can specify the generic type `PayableModel`:

    ```
        class MyModelPayable(Payable[MyModel]):
            ...
    ```
    """

    def __init__(self, model: PayableModel):
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
        try:
            self.model.refresh_from_db(fields=["payment"])
        except ObjectDoesNotExist:
            return None
        return self.payment

    @property
    @abstractmethod
    def payment_amount(self) -> Decimal:
        """The amount that should be paid for this model."""

    @property
    @abstractmethod
    def payment_topic(self) -> str:
        """A short description of what the payment is for.

        This will be saved to Payment.topic when a payment is created.
        """

    @property
    @abstractmethod
    def payment_notes(self) -> str:
        """Detailed notes about the payment.

        This will be saved to Payment.notes when a payment is created.
        """

    @property
    @abstractmethod
    def payment_payer(self) -> Member | None:
        """The member who paid or should pay for this model."""

    @property
    def tpay_allowed(self) -> bool:
        return True

    @property
    def paying_allowed(self) -> bool:
        return True

    @abstractmethod
    def can_manage_payment(self, member: Member) -> bool:
        """Return whether the given member can manage the payment for this payable."""

    @classproperty
    def immutable_after_payment(cls) -> bool:  # noqa: N805
        return False

    @classproperty
    def immutable_foreign_key_models(cls) -> dict[type[Model], str]:  # noqa: N805
        return {}

    @classproperty
    def immutable_model_fields_after_payment(cls) -> list[str]:  # noqa: N805
        return []

    def __hash__(self):
        return hash((self.payment_amount, self.payment_topic, self.payment_notes))


class Payables:
    def __init__(self):
        self._registry: dict[str, type[Payable]] = {}

    @lru_cache(maxsize=1024)
    def _get_key(self, model: Model | type[Model]):
        return f"{model._meta.app_label}.{model._meta.model_name}"

    def get_payable(self, model: Model) -> Payable:
        if self._get_key(model) not in self._registry:
            raise NotRegistered(f"No Payable registered for {self._get_key(model)}")
        return self._registry[self._get_key(model)](model)

    def get_payable_models(self) -> list[type[Model]]:
        """Return all registered models."""
        return [apps.get_model(key) for key in self._registry]

    def register(self, model: type[Model], payable_class: type[Payable]):
        """Register a payable class for a model.

        This sets up signals that ensure specified fields are not changed after payment.
        It also makes it possible to get a Payable instance given a model instance.
        """
        self._registry[self._get_key(model)] = payable_class
        if payable_class.immutable_after_payment:
            pre_save.connect(
                prevent_saving, sender=model, dispatch_uid=f"prevent_saving_{model}"
            )

            for foreign_model in payable_class.immutable_foreign_key_models:
                foreign_key_field = payable_class.immutable_foreign_key_models[
                    foreign_model
                ]
                pre_save.connect(
                    prevent_saving_related(foreign_key_field),
                    sender=foreign_model,
                    dispatch_uid=f"prevent_saving_related_{model}_{foreign_model}",
                )

    def _unregister(self, model: type[Model]):
        """Unregister a payable class for a model.

        This is for testing purposes only, to clean up the registry between tests.
        """
        payable_class = self._registry.get(self._get_key(model))
        if payable_class.immutable_after_payment:
            pre_save.disconnect(dispatch_uid=f"prevent_saving_{model}")
            for foreign_model in payable_class.immutable_foreign_key_models:
                pre_save.disconnect(
                    dispatch_uid=f"prevent_saving_related_{model}_{foreign_model}"
                )
        del self._registry[self._get_key(model)]


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
            raise PaymentError(
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
