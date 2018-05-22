"""Views provided by the payments package"""
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views import View

from payments import services
from .models import Payment


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('payments.process_payments'),
                  name='dispatch', )
class PaymentAdminView(View):
    """
    View that processes a payment
    """
    def get(self, request, *args, **kwargs):
        payment = Payment.objects.filter(pk=kwargs['pk'])
        result = services.process_payment(
            payment, kwargs['type']
        )

        if len(result) > 0:
            messages.success(request, _('Successfully processed %s.') %
                             model_ngettext(payment, 1))
        else:
            messages.error(request, _('Could not process %s.') %
                           model_ngettext(payment, 1))

        return redirect('admin:payments_payment_change', kwargs['pk'])
