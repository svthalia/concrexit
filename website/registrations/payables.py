from django.template.defaultfilters import date
from django.utils.functional import classproperty

from payments.payables import Payable, PayableModel, payables
from registrations.models import Registration, Renewal


class _EntryPayable(Payable[PayableModel]):
    """Abstract parent class for Registration- and RenewalPayables."""

    @property
    def payment_amount(self):
        return self.model.contribution

    @property
    def payment_payer(self):
        if self.model.membership:
            return self.model.membership.user
        return None

    @property
    def payment_notes(self):
        return f"{self.payment_topic}. Creation date: {date(self.model.created_at)}. Completion date: {date(self.model.updated_at)}"

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_model_fields_after_payment(self):
        return ["length", "contribution"]


class RegistrationPayable(_EntryPayable[Registration]):
    @property
    def payment_topic(self):
        return f"Membership registration {self.model.membership_type} ({self.model.length})"

    def can_manage_payment(self, member):
        return member and member.has_perm("registrations.change_registration")


class RenewalPayable(_EntryPayable[Renewal]):
    @property
    def payment_payer(self):
        return self.model.member

    @property
    def payment_topic(self):
        return f"Membership renewal {self.model.membership_type} ({self.model.length})"

    def can_manage_payment(self, member):
        return member and member.has_perm("registrations.change_renewal")


def register():
    payables.register(Renewal, RenewalPayable)
    payables.register(Registration, RegistrationPayable)
