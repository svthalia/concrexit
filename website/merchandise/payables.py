from django.utils.functional import classproperty

from merchandise.models import MerchandiseSale, MerchandiseSaleItem
from payments.payables import Payable, payables


class MerchandiseSalePayable(Payable):
    @property
    def payment_amount(self):
        return self.model.total_amount

    @property
    def payment_topic(self):
        return f"{self.model.sale_description}"

    @property
    def payment_notes(self):
        return f"{self.model.sale_description}"

    @property
    def payment_payer(self):
        return self.model.paid_by

    @property
    def paying_allowed(self):
        return True

    @property
    def tpay_allowed(self):
        return True

    @classproperty
    def immutable_after_payment(self):
        return True

    @classproperty
    def immutable_foreign_key_models(self):
        return {MerchandiseSaleItem: "sale"}

    @classproperty
    def immutable_model_fields_after_payment(self):
        return {
            MerchandiseSale: [
                "items",
                "sale_description",
                "total_amount",
                "paid_by",
            ],
            MerchandiseSaleItem: ["item", "sale", "total", "amount"],
        }

    def can_manage_payment(self, member):
        return True


def register():
    payables.register(MerchandiseSale, MerchandiseSalePayable)
