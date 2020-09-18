from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import (
    PermissionDenied,
    DisallowedRedirect,
    SuspiciousOperation,
)
from django.db.models import QuerySet, Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, FormView

from members.decorators import membership_required
from payments import services
from payments.exceptions import PaymentError
from payments.forms import BankAccountForm, PaymentCreateForm
from payments.models import BankAccount, Payment


@method_decorator(login_required, name="dispatch")
class BankAccountCreateView(SuccessMessageMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    success_url = reverse_lazy("payments:bankaccount-list")
    success_message = _("Bank account saved successfully.")

    def _derive_mandate_no(self) -> str:
        count = (
            BankAccount.objects.filter(owner=self.request.member)
            .exclude(mandate_no=None)
            .count()
            + 1
        )
        return f"{self.request.member.pk}-{count}"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["mandate_no"] = self._derive_mandate_no()
        context["creditor_id"] = settings.SEPA_CREDITOR_ID
        return context

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST["owner"] = self.request.member.pk
        if "direct_debit" in request.POST:
            request.POST["valid_from"] = timezone.now()
            request.POST["mandate_no"] = self._derive_mandate_no()
        else:
            request.POST["valid_from"] = None
            request.POST["mandate_no"] = None
            request.POST["signature"] = None
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: BankAccountForm) -> HttpResponse:
        BankAccount.objects.filter(owner=self.request.member, mandate_no=None).delete()
        BankAccount.objects.filter(owner=self.request.member).exclude(
            mandate_no=None
        ).update(valid_until=timezone.now())
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class BankAccountRevokeView(SuccessMessageMixin, UpdateView):
    model = BankAccount
    fields = ("valid_until",)
    success_url = reverse_lazy("payments:bankaccount-list")
    success_message = _("Direct debit authorisation successfully revoked.")

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .filter(owner=self.request.member, valid_until=None,)
            .exclude(mandate_no=None)
        )

    def get(self, *args, **kwargs) -> HttpResponse:
        return redirect("payments:bankaccount-list")

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST["valid_until"] = timezone.now()
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class BankAccountListView(ListView):
    model = BankAccount

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(owner=self.request.member)


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
                paid_by=self.request.member,
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
                "year": self.kwargs.get("year", timezone.now().year),
                "month": self.kwargs.get("month", timezone.now().month),
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class PaymentProcessView(SuccessMessageMixin, FormView):
    """
    Defines a view that allows the user to add a Thalia Pay payment to
    a Payable object using a POST request. The user should be
    authenticated.
    """

    form_class = PaymentCreateForm
    success_message = _("Your payment has been processed successfully.")
    template_name = "payments/payment_form.html"

    payable = None

    def get_success_url(self):
        return self.request.POST["next"]

    def dispatch(self, request, *args, **kwargs):
        if not request.member.tpay_enabled:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"payable": self.payable})
        return context

    def post(self, request, *args, **kwargs):
        if not (request.POST.keys() >= {"app_label", "model_name", "payable", "next"}):
            raise SuspiciousOperation("Missing POST parameters")

        if not url_has_allowed_host_and_scheme(
            request.POST["next"], allowed_hosts={request.get_host()}
        ):
            raise DisallowedRedirect

        app_label = request.POST["app_label"]
        model_name = request.POST["model_name"]
        payable_pk = request.POST["payable"]

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        self.payable = payable_model.objects.get(pk=payable_pk)

        if self.payable.payment_payer.pk != self.request.member.pk:
            messages.error(
                self.request, _("You are not allowed to process this payment.")
            )
            return redirect(request.POST["next"])

        if self.payable.payment:
            messages.error(self.request, _("This object has already been paid for."))
            return redirect(request.POST["next"])

        if "_save" not in request.POST:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            services.create_payment(self.payable, self.request.member, Payment.TPAY)
            self.payable.save()
        except PaymentError as e:
            messages.error(self.request, str(e))
        return super().form_valid(form)
