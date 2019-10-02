from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet, Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from members.decorators import membership_required
from payments.forms import BankAccountForm
from payments.models import BankAccount, Payment


@method_decorator(login_required, name='dispatch')
@method_decorator(membership_required, name='dispatch')
class BankAccountCreateView(SuccessMessageMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    success_url = reverse_lazy('payments:bankaccount-list')
    success_message = _('Bank account saved successfully.')

    def _derive_mandate_no(self) -> str:
        count = BankAccount.objects.filter(
            owner=self.request.member
        ).exclude(mandate_no=None).count() + 1
        return f'{self.request.member.pk}-{count}'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['mandate_no'] = self._derive_mandate_no()
        context['creditor_id'] = settings.SEPA_CREDITOR_ID
        return context

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST['owner'] = self.request.member.pk
        if 'direct_debit' in request.POST:
            request.POST['valid_from'] = timezone.now()
            request.POST['mandate_no'] = self._derive_mandate_no()
        else:
            request.POST['valid_from'] = None
            request.POST['mandate_no'] = None
            request.POST['signature'] = None
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: BankAccountForm) -> HttpResponse:
        BankAccount.objects.filter(
            owner=self.request.member, mandate_no=None).delete()
        BankAccount.objects.filter(
            owner=self.request.member
        ).exclude(mandate_no=None).update(valid_until=timezone.now())
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class BankAccountRevokeView(SuccessMessageMixin, UpdateView):
    model = BankAccount
    fields = ('valid_until',)
    success_url = reverse_lazy('payments:bankaccount-list')
    success_message = _('Direct debit authorisation successfully revoked.')

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(
            owner=self.request.member,
            valid_until=None,
        ).exclude(
            mandate_no=None
        )

    def get(self, *args, **kwargs) -> HttpResponse:
        return redirect('payments:bankaccount-list')

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST['valid_until'] = timezone.now()
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class BankAccountListView(ListView):
    model = BankAccount

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(owner=self.request.member)


@method_decorator(login_required, name='dispatch')
class PaymentListView(ListView):
    model = Payment

    def get_queryset(self) -> QuerySet:
        year = self.kwargs.get('year', timezone.now().year)
        month = self.kwargs.get('month', timezone.now().month)

        return super().get_queryset().filter(
            paid_by=self.request.member,
            processing_date__year=year,
            processing_date__month=month,
        )

    def get_context_data(self, *args, **kwargs):
        filters = []
        for i in range(13):
            new_now = timezone.now() - relativedelta(months=i)
            filters.append({
                'year': new_now.year, 'month': new_now.month
            })

        context = super().get_context_data(*args, **kwargs)
        context.update({
            'filters': filters,
            'total': context['object_list'].aggregate(
                Sum('amount')).get('amount__sum'),
            'year': self.kwargs.get('year', timezone.now().year),
            'month': self.kwargs.get('month', timezone.now().month)
        })
        return context
