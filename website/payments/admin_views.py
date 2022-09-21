"""Admin views provided by the payments package."""
import csv

from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import (
    DisallowedRedirect,
    PermissionDenied,
    SuspiciousOperation,
)
from django.db.models import Count, Max, Min, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.views import View

from sentry_sdk import capture_exception

from payments import payables, services

from .models import Batch, Payment, PaymentUser


@method_decorator(staff_member_required, name="dispatch")
class PaymentAdminView(View):
    """View that creates a payment."""

    def post(self, request, *args, app_label, model_name, payable, **kwargs):
        if "type" not in request.POST:
            raise SuspiciousOperation("Missing POST parameters")

        if "next" in request.POST and not url_has_allowed_host_and_scheme(
            request.POST.get("next"), allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        payable_obj = payables.get_payable(get_object_or_404(payable_model, pk=payable))

        if not payable_obj.can_manage_payment(request.member):
            raise PermissionDenied(_("You are not allowed to process this payment."))

        try:
            result = services.create_payment(
                payable_obj,
                self.request.member,
                request.POST["type"],
            )
            payable_obj.model.payment = result
            payable_obj.model.save()
        # pylint: disable=broad-except
        except Exception as e:
            capture_exception(e)
            messages.error(
                request,
                _("Something went wrong paying %s: %s")
                % (model_ngettext(payable_obj, 1), str(e)),
            )
            return redirect(f"admin:{app_label}_{model_name}_change", payable_obj.pk)

        if result:
            messages.success(
                request,
                _("Successfully paid %s.") % model_ngettext(payable_obj.model, 1),
            )
        else:
            messages.error(
                request,
                _("Could not pay %s.") % model_ngettext(payable_obj.model, 1),
            )
            return redirect(
                f"admin:{app_label}_{model_name}_change", payable_obj.model.pk
            )

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", result.pk)


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"),
    name="dispatch",
)
class BatchProcessAdminView(View):
    """View that processes a batch."""

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
            services.process_batch(batch)
            messages.success(
                request,
                _("Successfully processed {}.").format(model_ngettext(batch, 1)),
            )

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_batch_change", kwargs["pk"])


# todo: export using import-export library
@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"),
    name="dispatch",
)
class BatchExportAdminView(View):
    """View that exports a batch."""

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
                    bankaccount.name,
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
    permission_required("payments.process_batches"),
    name="dispatch",
)
class BatchTopicExportAdminView(View):
    """View that exports a batch per topic."""

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
    permission_required("payments.process_batches"),
    name="dispatch",
)
class BatchTopicDescriptionAdminView(View):
    """Shows the topic export as plain text."""

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

        date = batch.processing_date if batch.processing_date else timezone.now().date()
        description = f"Batch {batch.id} - {date}:\n"
        for row in topic_rows:
            min_date = timezone.localtime(row["min_date"]).date()
            max_date = timezone.localtime(row["max_date"]).date()
            description += f"- {row['topic']} ({row['count']}x) [{min_date} -- {max_date}], total €{row['total']:.2f}\n"
        description += f"\n{batch.description}"

        context["batch"] = batch
        context["description"] = description
        return render(request, self.template_name, context)


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_batches"),
    name="dispatch",
)
class BatchNewFilledAdminView(View):
    """View that adds a new batch filled with all payments that where not already in a batch."""

    def post(self, request, *args, **kwargs):
        batch = Batch()
        batch.save()

        payments = Payment.objects.filter(
            type=Payment.TPAY,
            batch=None,
        )

        payments.update(batch=batch)

        return redirect("admin:payments_batch_change", object_id=batch.id)
