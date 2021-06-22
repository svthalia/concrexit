from payments import Payable, payables
from sales.models.order import Order
from sales.services import is_manager


class OrderPayable(Payable):
    @property
    def payment_amount(self):
        return self.model.total_amount

    @property
    def payment_topic(self):
        return f"Sales at {self.model.shift}"

    @property
    def payment_notes(self):
        return f"{self.model.order_description}. Ordered at {self.model.created_at.time()} ({self.model.id})"

    @property
    def payment_payer(self):
        return self.model.payer

    def can_manage_payment(self, member):
        return is_manager(member, self.model.shift) and member.has_perm(
            "sales.change_order"
        )

    @property
    def immutable_after_payment(self):
        return True


def register():
    payables.register(Order, OrderPayable)
