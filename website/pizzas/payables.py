from django.template.defaultfilters import date

from payments import Payable, payables
from pizzas.models import FoodOrder
from pizzas.services import can_change_order


class FoodOrderPayable(Payable):
    @property
    def payment_amount(self):
        return self.model.product.price

    @property
    def payment_topic(self):
        start_date = date(self.model.food_event.start, "Y-m-d")
        return f"Food {self.model.food_event.event.title_en} [{start_date}]"

    @property
    def payment_notes(self):
        return (
            f"Food order by {self.model.member_name} "
            f"for {self.model.food_event.event.title_en}"
        )

    @property
    def payment_payer(self):
        return self.model.member

    def can_create_payment(self, member):
        return can_change_order(member, self.model.food_event)


def register():
    payables.register(FoodOrder, FoodOrderPayable)
