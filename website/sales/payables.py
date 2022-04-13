from django.utils.functional import classproperty

from payments import Payable, payables
from sales.models.order import Order, OrderItem
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

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_foreign_key_models(self):
        return {OrderItem: "order"}

    @classproperty
    def immutable_model_fields_after_payment(self):
        return {
            Order: [
                "items",
                "discount",
                "order_description",
                "subtotal",
                "total_amount",
                "payer",
                "shift",
            ],
            OrderItem: ["product", "order", "total", "amount"],
        }


def register():
    payables.register(Order, OrderPayable)
