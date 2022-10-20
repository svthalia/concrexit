from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import (
    DisallowedRedirect,
    PermissionDenied,
    SuspiciousOperation,
)
from django.db.models import QuerySet, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView, UpdateView

from dateutil.relativedelta import relativedelta

from payments import payables, services
from payments.exceptions import PaymentError
from payments.forms import BankAccountForm, BankAccountUserRevokeForm, PaymentCreateForm
from payments.models import BankAccount, Payment, PaymentUser


@method_decorator(login_required, name="dispatch")
class BankAccountCreateView(SuccessMessageMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    success_url = reverse_lazy("payments:bankaccount-list")
    success_message = _("Bank account saved successfully.")

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["mandate_no"] = services.derive_next_mandate_no(self.request.member)
        context["creditor_id"] = settings.SEPA_CREDITOR_ID
        return context

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST["owner"] = self.request.member.pk
        if "direct_debit" in request.POST:
            request.POST["valid_from"] = timezone.now()
            request.POST["mandate_no"] = services.derive_next_mandate_no(
                self.request.member
            )
        else:
            request.POST["valid_from"] = None
            request.POST["mandate_no"] = None
            request.POST["signature"] = None
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: BankAccountForm) -> HttpResponse:
        BankAccount.objects.filter(
            owner=PaymentUser.objects.get(pk=self.request.member.pk), mandate_no=None
        ).delete()
        BankAccount.objects.filter(
            owner=PaymentUser.objects.get(pk=self.request.member.pk)
        ).exclude(mandate_no=None).update(valid_until=timezone.now())
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class BankAccountRevokeView(SuccessMessageMixin, UpdateView):
    model = BankAccount
    form_class = BankAccountUserRevokeForm
    success_url = reverse_lazy("payments:bankaccount-list")
    success_message = _("Direct debit authorisation successfully revoked.")

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .filter(
                owner=PaymentUser.objects.get(pk=self.request.member.pk),
                valid_until=None,
            )
            .exclude(mandate_no=None)
        )

    def form_invalid(self, form):
        messages.error(
            self.request,
            _(
                "The mandate for this bank account cannot be revoked right now, as it is used for payments that have not yet been processed. Contact treasurer@thalia.nu to revoke your mandate."
            ),
        )
        super().form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, *args, **kwargs) -> HttpResponse:
        return redirect("payments:bankaccount-list")

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST["valid_until"] = timezone.now()
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class BankAccountListView(ListView):
    model = BankAccount

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "payment_user": PaymentUser.objects.get(pk=self.request.member.pk),
            }
        )
        return context

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .filter(owner=PaymentUser.objects.get(pk=self.request.member.pk))
        )


@method_decorator(login_required, name="dispatch")
class PaymentListView(ListView):
    model = Payment

    def get_queryset(self) -> QuerySet:
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        return (
            super()
            .get_queryset()
            .filter(
                paid_by=PaymentUser.objects.get(pk=self.request.member.pk),
                created_at__year=year,
                created_at__month=month,
            )
        )

    def get_context_data(self, *args, **kwargs):
        filters = []
        for i in range(13):
            new_now = timezone.now() - relativedelta(months=i)
            filters.append({"year": new_now.year, "month": new_now.month})

        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "filters": filters,
                "total": context["object_list"]
                .aggregate(Sum("amount"))
                .get("amount__sum"),
                "tpay_balance": PaymentUser.objects.get(
                    pk=self.request.member.pk
                ).tpay_balance,
                "year": self.kwargs.get("year", timezone.now().year),
                "month": self.kwargs.get("month", timezone.now().month),
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class PaymentProcessView(SuccessMessageMixin, FormView):
    """Defines a view that allows the user to add a Thalia Pay payment to a Payable object using a POST request.

    The user should be authenticated.
    """

    form_class = PaymentCreateForm
    success_message = _("Your payment has been processed successfully.")
    template_name = "payments/payment_form.html"

    payable = None

    def get_success_url(self):
        return self.request.POST["next"]

    def dispatch(self, request, *args, **kwargs):
        if not PaymentUser.objects.get(pk=request.member.pk).tpay_enabled:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.payable is None:
            raise Http404("Payable does not exist")
        context = super().get_context_data(**kwargs)
        context.update({"payable": self.payable})
        context.update({"payable_hash": hash(self.payable)})
        context.update(
            {
                "new_balance": PaymentUser.objects.get(
                    pk=self.payable.payment_payer.pk
                ).tpay_balance
                - Decimal(self.payable.payment_amount)
            }
        )
        return context

    def _check_payment_allowed(self, request, payable_hash):
        if (
            self.payable.payment_payer.pk
            != PaymentUser.objects.get(pk=self.request.member.pk).pk
        ):
            return _("You are not allowed to process this payment.")

        if self.payable.payment_amount == 0:
            return _("No payment required for amount of €0.00")

        if self.payable.payment:
            return _("This object has already been paid for.")

        if not self.payable.tpay_allowed:
            return _("You are not allowed to use Thalia Pay for this payment.")

        if str(hash(self.payable)) != str(payable_hash):
            return _(
                "This object has been changed in the mean time. You have not paid."
            )

        return None

    def post(self, request, *args, **kwargs):
        if not (
            request.POST.keys()
            >= {"app_label", "model_name", "payable", "payable_hash", "next"}
        ):
            raise SuspiciousOperation("Missing POST parameters")

        if not url_has_allowed_host_and_scheme(
            request.POST["next"], allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        app_label = request.POST["app_label"]
        model_name = request.POST["model_name"]
        payable_pk = request.POST["payable"]
        payable_hash = request.POST["payable_hash"]

        try:
            payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError as error:
            raise Http404("This app model does not exist.") from error

        try:
            payable_obj = payable_model.objects.get(pk=payable_pk)
        except payable_model.DoesNotExist as error:
            raise Http404("This payable does not exist.") from error

        self.payable = payables.get_payable(payable_obj)

        error = self._check_payment_allowed(request, payable_hash)
        if error:
            messages.error(self.request, error)
            return redirect(request.POST["next"])

        if "_save" not in request.POST:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            services.create_payment(
                self.payable,
                PaymentUser.objects.get(pk=self.request.member.pk),
                Payment.TPAY,
            )
            self.payable.model.save()
        except PaymentError as e:
            messages.error(self.request, str(e))
        return super().form_valid(form)
