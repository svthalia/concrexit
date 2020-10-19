"""Admin views provided by the payments package"""
import csv

from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Sum, Count, Min, Max
from django.http import HttpResponse
from django.core.exceptions import SuspiciousOperation, DisallowedRedirect
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View

from payments import services
from .models import Payment, Batch, PaymentUser


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_payments"), name="dispatch",
)
class PaymentAdminView(View):
    """
    View that creates a payment
    """

    def post(self, request, *args, app_label, model_name, payable, **kwargs):
        if "type" not in request.POST:
            raise SuspiciousOperation("Missing POST parameters")

        if "next" in request.POST and not url_has_allowed_host_and_scheme(
            request.POST.get("next"), allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        payable_obj = payable_model.objects.get(pk=payable)

        result = services.create_payment(
            payable_obj, self.request.member, request.POST["type"],
        )
        payable_obj.save()

        if result:
            messages.success(
                request, _("Successfully paid %s.") % model_ngettext(payable_obj, 1),
            )
        else:
            messages.error(
                request, _("Could not pay %s.") % model_ngettext(payable_obj, 1),
            )
            return redirect(f"admin:{app_label}_{model_name}_change", payable_obj.pk)

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", result.pk)


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

        if "next" in request.POST and not url_has_allowed_host_and_scheme(
            request.POST.get("next"), allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        if batch.processed:
            messages.error(
                request, _("{} already processed.").format(model_ngettext(batch, 1))
            )
        else:
            batch.processed = True
            payments = batch.payments_set.select_related("paid_by")
            for payment in payments:
                bank_account = payment.paid_by.bank_accounts.last()
                bank_account.last_used = timezone.now()
                bank_account.save()

            batch.save()

            services.send_tpay_batch_processing_emails(batch)

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
            _("Account holder"),
            _("IBAN"),
            _("Mandate Reference"),
            _("Amount"),
            _("Description"),
            _("Mandate Date"),
        ]
        writer.writerow([capfirst(x) for x in headers])

        member_rows = batch.payments_set.values("paid_by").annotate(total=Sum("amount"))

        for row in member_rows:
            member = PaymentUser.objects.get(id=row["paid_by"])
            bankaccount = member.bank_accounts.last()
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
class BatchTopicExportAdminView(View):
    """
    View that exports a batch per topic
    """

    def post(self, request, *args, **kwargs):
        batch = Batch.objects.get(pk=kwargs["pk"])

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment;filename="batch-topic.csv"'
        writer = csv.writer(response)
        headers = [
            _("Topic"),
            _("No. of payments"),
            _("First payment"),
            _("Last payment"),
            _("Total amount"),
        ]
        writer.writerow([capfirst(x) for x in headers])

        topic_rows = (
            batch.payments_set.values("topic")
            .annotate(
                total=Sum("amount"),
                count=Count("paid_by"),
                min_date=Min("created_at"),
                max_date=Max("created_at"),
            )
            .order_by("topic")
        )

        for row in topic_rows:
            writer.writerow(
                [
                    row["topic"],
                    row["count"],
                    timezone.localtime(row["min_date"]).date(),
                    timezone.localtime(row["max_date"]).date(),
                    f"{row['total']:.2f}",
                ]
            )
        return response


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"), name="dispatch",
)
class BatchTopicDescriptionAdminView(View):
    """
    Shows the topic export as plain text
    """

    template_name = "admin/payments/batch_topic.html"

    def post(self, request, *args, **kwargs):
        context = {}
        batch = get_object_or_404(Batch, pk=kwargs["pk"])
        topic_rows = (
            batch.payments_set.values("topic")
            .annotate(
                total=Sum("amount"),
                count=Count("paid_by"),
                min_date=Min("created_at"),
                max_date=Max("created_at"),
            )
            .order_by("topic")
        )

        description = f"Batch {batch.id} - {batch.processing_date if batch.processing_date else timezone.now().date()}:\n"
        for row in topic_rows:
            description += f"- {row['topic']} ({row['count']}x) [{timezone.localtime(row['min_date']).date()} -- {timezone.localtime(row['max_date']).date()}], total €{row['total']:.2f}\n"
        description += f"\n{batch.description}"

        context["batch"] = batch
        context["description"] = description
        return render(request, self.template_name, context)


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
