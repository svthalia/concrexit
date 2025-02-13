from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone

from payments.models import BankAccount
from reimbursements.emails import send_verdict_email

from . import models


class ReimbursementForm(forms.ModelForm):
    class Meta:
        model = models.Reimbursement
        fields = "__all__"

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

    form = ReimbursementForm

    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        if request.member and request.member.bank_accounts.exists():
            form.base_fields[
                "confirm_iban"
            ].help_text = request.member.bank_accounts.last().iban
        return form

    def save_model(self, request, obj, form, change):
        # TODO: add immediate push to moneybird if approved.
        if not obj.owner_id:
            obj.owner_id = request.user.id

        bank = BankAccount.objects.filter(owner=obj.owner).last()

        if bank is None and not bank.valid_until <= timezone.now():
            raise ValidationError(
                "You must have a valid bank account to request a reimbursement."
            )

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
