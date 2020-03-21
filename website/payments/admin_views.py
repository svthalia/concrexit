"""Admin views provided by the payments package"""
import csv
import datetime

from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.utils.decorators import method_decorator
from django.views import View

from members.models import Member
from payments import services
from .models import Payment, Batch, BankAccount


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_payments"), name="dispatch",
)
class PaymentAdminView(View):
    """
    View that processes a payment
    """

    def post(self, request, *args, **kwargs):
        payment = Payment.objects.filter(pk=kwargs["pk"])

        if not ("type" in request.POST):
            return redirect("admin:payments_payment_change", kwargs["pk"])

        result = services.process_payment(payment, request.member, request.POST["type"])

        if len(result) > 0:
            messages.success(
                request, _("Successfully processed %s.") % model_ngettext(payment, 1)
            )
        else:
            messages.error(
                request, _("Could not process %s.") % model_ngettext(payment, 1)
            )

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", kwargs["pk"])


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"), name="dispatch",
)
class BatchProcessAdminView(View):
    """
    View that processes a batch
    """

    def post(self, request, *args, **kwargs):
        batch = Batch.objects.get(pk=kwargs["pk"])

        if batch.processed:
            messages.error(
                request, _("{} already processed.").format(model_ngettext(batch, 1))
            )
        else:
            batch.processed = True
            payments = batch.payments_set.select_related("paid_by")
            for payment in payments:
                ba = payment.paid_by.bank_accounts.last()
                ba.last_used = timezone.now()
                ba.save()

            batch.save()
            messages.success(
                request,
                _("Successfully processed {}.").format(model_ngettext(batch, 1)),
            )

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_batch_change", kwargs["pk"])


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"), name="dispatch",
)
class BatchExportAdminView(View):
    """
    View that exports a batch
    """

    def post(self, request, *args, **kwargs):
        batch = Batch.objects.get(pk=kwargs["pk"])

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="batch.csv"'
        writer = csv.writer(response)
        headers = [
            _("Account holder name"),
            _("IBAN"),
            _("Mandate id"),
            _("Amount"),
            _("Description"),
            _("Mandate date"),
        ]
        writer.writerow([capfirst(x) for x in headers])

        member_rows = batch.payments_set.values("paid_by").annotate(total=Sum("amount"))

        for row in member_rows:
            member: Member = Member.objects.get(id=row["paid_by"])
            bankaccount: BankAccount = member.bank_accounts.last()
            writer.writerow(
                [
                    member.get_full_name(),
                    bankaccount.iban,
                    bankaccount.mandate_no,
                    f"{row['total']:.2f}",
                    batch.description,
                    bankaccount.valid_from,
                ]
            )
        return response


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"), name="dispatch",
)
class BatchNewFilledAdminView(View):
    """
    View that adds a new batch filled with all payments that where not already in a batch.
    """

    def get(self, request, *args, **kwargs):
        batch = Batch()
        batch.save()

        payments = Payment.objects.filter(type=Payment.TPAY, batch=None,)

        payments.update(batch=batch)

        return redirect("admin:payments_batch_change", object_id=batch.id)
