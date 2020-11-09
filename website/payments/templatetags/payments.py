from django import template
from django.contrib.contenttypes.models import ContentType

from payments.exceptions import PaymentError
from payments.models import Payable, PaymentUser

register = template.Library()


@register.inclusion_tag("payments/templatetags/payment_button.html")
def payment_button(payable: Payable, redirect_to: str):
    if payable.pk is None:
        raise PaymentError("Payable does not exist")

    content_type = ContentType.objects.get_for_model(payable)

    return {
        "member": PaymentUser.objects.get(pk=payable.payment_payer.pk)
        if payable.payment_payer
        else None,
        "pk": payable.pk,
        "app_label": content_type.app_label,
        "model_name": content_type.model,
        "redirect_to": redirect_to,
    }
