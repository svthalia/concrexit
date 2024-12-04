from django.contrib import admin
from django.utils import timezone

from utils.snippets import send_email

from . import models


@admin.register(models.Reimbursement)
class ReimbursementsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "owner",
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

    readonly_fields = [
        "evaluated_by",
        "evaluated_at",
        "created",
        "owner",
    ]

    def send_verdict_email(self, obj):
        send_email(
            to=[obj.owner.email],
            subject="Reimbursement request",
            txt_template="reimbursements/email/verdict.txt",
            html_template="reimbursements/email/verdict.html",
            context={
                "first_name": obj.owner.profile.firstname,
                "description": obj.description,
                "verdict": obj.verdict,
                "verdict_clarification": obj.verdict_clarification,
            },
        )

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            obj.evaluated_by = request.user
            obj.evaluated_at = timezone.now()

            # TODO: add moneybird integration

        super().save_model(request, obj, form, change)

        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            self.send_verdict_email(obj)

    def get_readonly_fields(self, request, obj=None):
        readonly = self.readonly_fields
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
