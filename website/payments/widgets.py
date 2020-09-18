"""Widgets provided by the payments package"""
from django.contrib.contenttypes.models import ContentType
from django.forms import Widget

from payments.models import Payment


class PaymentWidget(Widget):
    """
    Custom widget for the Payment object, used in registrations
    """

    template_name = "payments/widgets/payment.html"
    obj = None

    def __init__(self, attrs=None, obj=None):
        super().__init__(attrs)
        self.obj = obj

    def get_context(self, name, value, attrs) -> dict:
        context = super().get_context(name, value, attrs)
        if self.obj and not value:
            context["obj"] = self.obj
            context["content_type"] = ContentType.objects.get_for_model(self.obj)
        elif value:
            payment = Payment.objects.get(pk=value)
            context["url"] = payment.get_admin_url()
            context["payment"] = payment
        return context

    class Media:
        js = ("admin/payments/js/payments.js",)


class SignatureWidget(Widget):
    """
    Widget for signature image
    """

    template_name = "payments/widgets/signature.html"

    class Media:
        js = (
            "payments/js/signature_pad.min.js",
            "payments/js/main.js",
        )
        css = {"all": ("admin/payments/css/signature.css",)}
