"""Widgets provided by the payments package."""
from django.contrib.contenttypes.models import ContentType
from django.forms import Widget

from payments import payables
from payments.models import Payment, PaymentUser


class PaymentWidget(Widget):
    """Custom widget for the Payment object, used in registrations."""

    template_name = "payments/widgets/payment.html"

    def __init__(self, attrs=None, obj=None):
        super().__init__(attrs)
        self.obj = obj

    def get_context(self, name, value, attrs) -> dict:
        context = super().get_context(name, value, attrs)
        if self.obj and not value:
            payable = payables.get_payable(self.obj)
            context["obj"] = payable
            context["payable_payer"] = (
                PaymentUser.objects.get(pk=payable.payment_payer.pk)
                if getattr(payable, "payment_payer", None) is not None
                else None
            )
            context["content_type"] = ContentType.objects.get_for_model(self.obj)
        elif value:
            payment = Payment.objects.get(pk=value)
            context["url"] = payment.get_admin_url()
            context["payment"] = payment
        return context

    class Media:
        js = ("admin/payments/js/payments.js",)


class SignatureWidget(Widget):
    """Widget for signature image."""

    template_name = "payments/widgets/signature.html"

    class Media:
        js = (
            "payments/js/signature_pad.min.js",
            "payments/js/main.js",
        )
        css = {"all": ("admin/payments/css/signature.css",)}
