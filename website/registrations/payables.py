from django.template.defaultfilters import date

from payments.payables import Payable, payables
from registrations.models import Renewal, Registration, Entry


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

    def can_create_payment(self, member):
        return False


class RegistrationPayable(EntryPayable):
    @property
    def payment_topic(self):
        return f"Membership registration {self.model.membership_type} ({self.model.length})"


class RenewalPayable(EntryPayable):
    @property
    def payment_payer(self):
        return self.model.member

    @property
    def payment_topic(self):
        return f"Membership renewal {self.model.membership_type} ({self.model.length})"


def register():
    payables.register(Entry, EntryPayable)
    payables.register(Renewal, RenewalPayable)
    payables.register(Registration, RegistrationPayable)
