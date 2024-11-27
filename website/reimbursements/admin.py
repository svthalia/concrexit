from django.contrib import admin
from django.contrib.admin import register
from django.utils import timezone

from reimbursements import models
from utils.snippets import send_email


@register(models.Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "owner",
        "date_incurred",
        "amount",
        "verdict",
        "evaluated_by",
    )
    list_filter = ("verdict", "created", "date_incurred", "owner")

    autocomplete_fields = ["owner"]
    readonly_fields = [
        "evaluated_by",
        "evaluated_at",
        "created",
        "amount",
        "receipt",
        "owner",
        "date_incurred",
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
        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            obj.evaluated_by = request.user
            obj.evaluated_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            self.send_verdict_email(obj)

    def get_readonly_fields(self, obj=None):
        if not obj or obj.verdict:
            return self.readonly_fields + [
                "verdict",
                "description",
            ]
        return self.readonly_fields

    def get_queryset(self, request):
        if request.user.has_perm("reimbursements.view_reimbursement"):
            return super().get_queryset(request)
        return models.Reimbursement.objects.filter(owner=request.user)

    def has_view_permission(self, request, obj=None) -> bool:
        if obj and request.member and obj.owner == request.member:
            return True
        return super().has_view_permission(request, obj)
