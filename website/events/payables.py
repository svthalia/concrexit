from django.template.defaultfilters import date
from django.utils.functional import classproperty

from events.models import EventRegistration
from events.services import is_organiser
from payments.payables import Payable, payables


class EventRegistrationPayable(Payable[EventRegistration]):
    @property
    def payment_amount(self):
        return self.model.payment_amount

    @property
    def payment_topic(self):
        return f'{self.model.event.title} [{date(self.model.event.start, "Y-m-d")}]'

    @property
    def payment_notes(self):
        notes = f"Event registration {self.model.event.title}. "
        notes += f"{date(self.model.event.start)}. Registration date: {date(self.model.date)}."
        if self.model.special_price:
            notes += " [special price]"
        return notes

    @property
    def payment_payer(self):
        return self.model.member

    def can_manage_payment(self, member):
        return is_organiser(member, self.model.event) and member.has_perm(
            "events.change_eventregistration"
        )

    @property
    def tpay_allowed(self):
        return self.model.event.tpay_allowed

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_model_fields_after_payment(self):
        return ["member", "event", "name", "payment_amount"]


def register():
    payables.register(EventRegistration, EventRegistrationPayable)
