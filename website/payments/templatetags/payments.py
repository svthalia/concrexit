from django import template
from django.db.models import Model

from payments import payables
from payments.exceptions import PaymentError
from payments.models import PaymentUser

register = template.Library()


@register.inclusion_tag("payments/templatetags/payment_button.html")
def payment_button(model: Model, redirect_to: str):
    if model.pk is None:
        raise PaymentError("Payable does not exist")

    payable = payables.get_payable(model)

    return {
        "member": PaymentUser.objects.get(pk=payable.payment_payer.pk)
        if payable.payment_payer
        else None,
        "payable": payable,
        "app_label": model._meta.app_label,
        "model_name": model._meta.model_name,
        "redirect_to": redirect_to,
    }
