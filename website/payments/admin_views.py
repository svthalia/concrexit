"""Admin views provided by the payments package"""
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
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
            "app_label" in kwargs
            and "model_name" in kwargs
            and "payable" in kwargs
            and "type" in request.POST
        ):
            raise SuspiciousOperation("Missing POST parameters")
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
