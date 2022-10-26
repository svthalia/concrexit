from django.template.defaultfilters import date
from django.utils.functional import classproperty

from payments.payables import Payable, payables
from registrations.models import Entry, Registration, Renewal


class EntryPayable(Payable):
    @property
    def payment_amount(self):
        return self.model.contribution

    @property
    def payment_payer(self):
        if self.model.membership:
            return self.model.membership.user
        return None

    @property
    def payment_topic(self):
        return "Registration entry"

    @property
    def payment_notes(self):
        return f"{self.payment_topic}. Creation date: {date(self.model.created_at)}. Completion date: {date(self.model.updated_at)}"

    def can_manage_payment(self, member):
        return member and member.has_perm("registrations.change_entry")

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_model_fields_after_payment(self):
        return ["length", "contribution"]


class RegistrationPayable(EntryPayable):
    @property
    def payment_topic(self):
        return f"Membership registration {self.model.membership_type} ({self.model.length})"

    def can_manage_payment(self, member):
        return member and member.has_perm("registrations.change_registration")


class RenewalPayable(EntryPayable):
    @property
    def payment_payer(self):
        return self.model.member

    @property
    def payment_topic(self):
        return f"Membership renewal {self.model.membership_type} ({self.model.length})"

    def can_manage_payment(self, member):
        return member and member.has_perm("registrations.change_renewal")


def register():
    payables.register(Entry, EntryPayable)
    payables.register(Renewal, RenewalPayable)
    payables.register(Registration, RegistrationPayable)
