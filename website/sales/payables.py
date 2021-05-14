from payments import Payable, payables
from sales.models.order import Order


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

    def can_create_payment(self, member):
        return True


def register():
    payables.register(Order, OrderPayable)
