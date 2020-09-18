"""Admin views provided by the payments package"""
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import SuspiciousOperation, DisallowedRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View

from payments import services


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_payments"), name="dispatch",
)
class PaymentAdminView(View):
    """
    View that creates a payment
    """

    def post(self, request, *args, app_label, model_name, payable_model, **kwargs):
        if "type" not in request.POST:
            raise SuspiciousOperation("Missing POST parameters")

        if "next" in request.POST and not url_has_allowed_host_and_scheme(
            request.POST.get("next"), allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        payable_model = payable_model.objects.get(pk=payable_model)

        result = services.create_payment(
            payable_model, request.member, request.POST["type"]
        )
        payable_model.save()

        if result:
            messages.success(
                request, _("Successfully paid %s.") % model_ngettext(payable_model, 1),
            )
        else:
            messages.error(
                request, _("Could not pay %s.") % model_ngettext(payable_model, 1),
            )
            return redirect(f"admin:{app_label}_{model_name}_change", payable_model.pk)

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", result.pk)
