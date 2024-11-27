from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from reimbursements.models import Reimbursement


class IndexView(LoginRequiredMixin, ListView):
    model = Reimbursement
    template_name = "reimbursements/index.html"

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class CreateReimbursementView(CreateView):
    model = Reimbursement
    template_name = "reimbursements/create.html"

    fields = ["date_incurred", "amount", "description", "receipt"]

    success_url = reverse_lazy("reimbursements:index")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["form"].fields["date_incurred"].widget.input_type = "date"
        return context
