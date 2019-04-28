from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from members.decorators import membership_required
from payments.forms import BankAccountForm
from payments.models import BankAccount


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
        return super().get_queryset().filter(owner=self.request.member)

    def get(self, **kwargs) -> HttpResponse:
        raise Http404

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST['valid_until'] = timezone.now()
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class BankAccountListView(ListView):
    model = BankAccount

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(owner=self.request.member)
