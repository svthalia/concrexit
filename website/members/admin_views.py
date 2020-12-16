"""Admin views provided by the members package."""
import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View

from members.models import Member


@method_decorator(staff_member_required, "dispatch")
@method_decorator(permission_required("auth.change_user"), "dispatch")
class IbanExportView(View):
    """Exports IBANs of users that have set auto renew to true in their accounts."""

    def get(self, request, **kwargs) -> HttpResponse:
        header_fields = ["name", "username", "iban", "bic"]
        rows = []

        members = Member.current_members.filter(profile__auto_renew=True)

        for member in members:
            if (
                member.current_membership.type != "honorary"
                and member.bank_accounts.exists()
            ):
                bank_account = member.bank_accounts.last()
                rows.append(
                    {
                        "name": bank_account.name,
                        "username": member.username,
                        "iban": bank_account.iban,
                        "bic": bank_account.bic,
                    }
                )

        response = HttpResponse(content_type="text/csv")
        writer = csv.DictWriter(response, header_fields)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        response["Content-Disposition"] = 'attachment; filename="iban-export.csv"'
        return response
