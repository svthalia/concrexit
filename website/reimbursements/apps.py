from django.contrib import admin
from django.contrib.admin import register
from django.utils import timezone

from reimbursements import models


@register(models.Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "owner",
        "date_incurred",
        "amount",
        "verdict",
    )
    list_filter = ("approved", "created", "date_incurred", "owner")

    autocomplete_fields = ["owner"]
    readonly_fields = ["approved_by", "approved_at", "created", "updated"]

    def save_model(self, request, obj, form, change):
        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            obj.evaluated_by = request.user
            obj.evaluated_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.verdict is not None and obj.verdict != form.initial["verdict"]:
            # TODO: Send verdict conclusion e-mail to requester
            pass

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.approved:
            return self.readonly_fields + [
                "approved",
                "amount",
                "description",
                "receipt",
                "date_incurred",
                "owner",
            ]
        return self.readonly_fields
