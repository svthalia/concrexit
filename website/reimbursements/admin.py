from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from moneybirdsynchronization.tasks import synchronize_moneybird_reimbursement
from reimbursements.emails import send_verdict_email

from . import models


class ReimbursementForm(forms.ModelForm):
    class Meta:
        model = models.Reimbursement
        fields = ["amount", "date_incurred", "description", "receipt", "confirm_iban"]

    confirm_iban = forms.BooleanField(required=True)


@admin.register(models.Reimbursement)
class ReimbursementsAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "created",
        "date_incurred",
        "amount",
        "verdict",
        "evaluated_by",
    )
    list_filter = ("verdict", "created", "date_incurred")
    search_fields = (
        "date_incurred",
        "owner__first_name",
        "owner__last_name",
        "description",
    )

    def save_model(self, request, obj, form, change):
        if obj.verdict is not None and change:
            obj.evaluated_by = request.user
            obj.evaluated_at = timezone.now()

        if obj.verdict == obj.Verdict.APPROVED or obj.verdict == obj.Verdict.DENIED:
            if not obj.evaluated_by:
                raise ValidationError("You must provide the evaluator.")
            if not obj.evaluated_at:
                raise ValidationError("You must provide the evaluation date.")

        super().save_model(request, obj, form, change)

        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            send_verdict_email(obj)

            if obj.verdict == obj.Verdict.APPROVED:
                transaction.on_commit(
                    lambda: synchronize_moneybird_reimbursement.delay(obj.id)
                )

    def get_readonly_fields(self, request, obj=None):
        readonly = [
            "created",
            "owner",
        ]
        if obj:
            readonly += [
                "description",
                "amount",
                "date_incurred",
                "receipt",
            ]
        if not obj or obj.verdict:
            readonly += [
                "verdict",
                "verdict_clarification",
                "evaluated_by",
                "evaluated_at",
            ]
        return readonly

    def get_queryset(self, request):
        if request.user.has_perm("reimbursements.change_reimbursement"):
            return super().get_queryset(request)
        return models.Reimbursement.objects.filter(owner=request.user)

    def has_view_permission(self, request, obj=None) -> bool:
        if obj and request.member and obj.owner == request.member:
            return True
        return super().has_view_permission(request, obj)

    def add_view(self, request, **kwargs):
        """View for setting study status.

        This is implemented within the ModelAdmin because the admin templates require
        complicated logic that is not easily implemented in a separate FormView.
        """
        app_label = self.opts.app_label

        if not request.user.has_perm("reimbursements.add_reimbursement"):
            raise PermissionError

        if request.POST:
            form = ReimbursementForm(
                request.POST,
                request.FILES,
                initial={"owner": request.user},
            )
            form["confirm_iban"].help_text = request.member.bank_accounts.last().iban
            if form.is_valid():
                form.instance.owner = request.user
                form.save()
                self.message_user(request, "Succesfully created a reimbursement.")
                return redirect("admin:reimbursements_reimbursement_changelist")
        else:
            form = ReimbursementForm()
            form["confirm_iban"].help_text = request.member.bank_accounts.last().iban

        context = {
            **self.admin_site.each_context(request),
            "module_name": "Reimbursements",
            "title": "Create a reimbursement",
            "subtitle": None,
            "opts": self.opts,
            "app_label": app_label,
            "media": self.media,
            "form": form,
        }

        return TemplateResponse(
            request,
            "admin/reimbursements/reimbursement/add.html",
            context,
        )
