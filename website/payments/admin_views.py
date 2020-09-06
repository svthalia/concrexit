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

    def post(self, request, *args, **kwargs):
        if not (
            kwargs.keys() >= {"app_label", "model_name", "payable"}
            and "type" in request.POST
        ):
            raise SuspiciousOperation("Missing POST parameters")

        if "next" in request.POST and not url_has_allowed_host_and_scheme(
            request.POST.get("next"), allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        app_label = kwargs["app_label"]
        model_name = kwargs["model_name"]

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        payable = payable_model.objects.get(pk=kwargs["payable"])

        result = services.create_payment(payable, request.member, request.POST["type"])
        payable.save()

        if result:
            messages.success(
                request, _("Successfully paid %s.") % model_ngettext(payable, 1),
            )
        else:
            messages.error(
                request, _("Could not pay %s.") % model_ngettext(payable, 1),
            )
            return redirect(f"admin:{app_label}_{model_name}_change", payable.pk)

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", result.pk)
