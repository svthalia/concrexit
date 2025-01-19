from django import forms
from django.contrib import admin
from django.utils import timezone

from reimbursements.emails import send_verdict_email

from . import models


class ReimbursementForm(forms.ModelForm):
    class Meta:
        model = models.Reimbursement
        fields = "__all__"

    def clean(self):
        if not self.instance.owner:
            self.instance.owner = self.request.user

        if self.cleaned_data["verdict"] != self.initial["verdict"]:
            self.instance.evaluated_by = self.request.user
            self.instance.evaluated_at = timezone.now()

        return super().clean()


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
        form.request = request
        return form

    def save_model(self, request, obj, form, change):
        # TODO: add immediate push to moneybird if approved.

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
                "iban",
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
