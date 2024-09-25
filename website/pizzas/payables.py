from django.template.defaultfilters import date
from django.utils.functional import classproperty

from payments.payables import Payable, payables
from pizzas.models import FoodOrder
from pizzas.services import can_change_order


class FoodOrderPayable(Payable[FoodOrder]):
    @property
    def payment_amount(self):
        return self.model.product.price

    @property
    def payment_topic(self):
        start_date = date(self.model.food_event.start, "Y-m-d")
        return f"Food {self.model.food_event.event.title} [{start_date}]"

    @property
    def payment_notes(self):
        return (
            f"Food order by {self.model.member_name} "
            f"for {self.model.food_event.event.title}"
        )

    @property
    def payment_payer(self):
        return self.model.member

    def can_manage_payment(self, member):
        return can_change_order(member, self.model.food_event)

    @property
    def tpay_allowed(self):
        return self.model.food_event.tpay_allowed

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_model_fields_after_payment(self):
        return ["product", "food_event", "name", "member"]


def register():
    payables.register(FoodOrder, FoodOrderPayable)
