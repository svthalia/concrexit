"""Widgets provided by the payments package"""
from django.forms import Widget

from payments.models import Payment


class PaymentWidget(Widget):
    """
    Custom widget for the Payment object, used in registrations
    """
    template_name = 'payments/widget.html'

    def value_from_datadict(self, data, files, name):
        return super().value_from_datadict(data, files, name)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            payment = Payment.objects.get(pk=value)
            context['url'] = payment.get_admin_url()
            context['processed'] = payment.processed
        return context
