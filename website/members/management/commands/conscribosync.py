import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.defaultfilters import date
from django.utils import translation

from requests import HTTPError

from members.models import Member
from utils.conscribo.api import ConscriboApi
from utils.conscribo.objects import Command as ApiCommand
from utils.conscribo.objects import ResultException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """This command can be executed periodically to sync the bank accounts of members with the financial administration."""

    def handle(self, *args, **options):
        api = ConscriboApi(
            settings.CONSCRIBO_ACCOUNT,
            settings.CONSCRIBO_USER,
            settings.CONSCRIBO_PASSWORD,
        )

        try:
            relations_response = api.single_request(
                "listRelations",
                entityType="lid_2",
                requestedFields={"fieldName": ["website_id", "code"]},
            )
            relations_response.raise_for_status()
            relations_response = relations_response.data

            current_relations = {}
            if len(relations_response.get("relations")) > 0:
                current_relations = {
                    int(r.get("website_id")): r.get("code", None)
                    for r in relations_response.get("relations").values()
                    if r.get("website_id", "") != ""
                }

            replace_commands = []
            with translation.override("nl"):
                for member in Member.current_members.all():
                    code = current_relations.pop(member.pk, None)
                    profile = member.profile

                    if member.bank_accounts.exists():
                        account = member.bank_accounts.last()
                        mandate_no = account.mandate_no
                        mandate_date = date(account.created_at, "Y-m-d")
                        bank_account = {
                            "name": account.name,
                            "bic": account.bic or "",
                            "iban": account.iban,
                        }
                    else:
                        mandate_no = ""
                        mandate_date = ""
                        bank_account = {
                            "name": "",
                            "bic": "",
                            "iban": "",
                        }

                    fields = {
                        "website_id": member.pk,
                        "voornaam": member.first_name,
                        "naam": member.last_name[:100],  # api maxlength: 100
                        "einddatum_lidmaatschap": date(
                            member.current_membership.until, "Y-m-d"
                        ),
                        "e_mailadres": member.email,
                        "eerste_adresregel": profile.address_street,
                        "tweede_adresregel": profile.address_street2,
                        "postcode": profile.address_postal_code,
                        "plaats": profile.address_city,
                        "land": profile.get_address_country_display(),
                        "bankrekeningnummer": bank_account,
                        "machtigingskenmerk": mandate_no,
                        "machtigingsdatum": mandate_date,
                    }

                    replace_commands.append(
                        ApiCommand(
                            command="ReplaceRelation",
                            entityType="lid_2",
                            fields=fields,
                            code=code,
                        )
                    )

            replace_responses = api.multi_request(replace_commands)
            for response in replace_responses:
                if not response.success:
                    logger.debug(response.notifications)

            delete_commands = []
            for code in current_relations.values():
                delete_commands.append(
                    ApiCommand(
                        command="DeleteRelation",
                        entityType="lid_2",
                        code=code,
                    )
                )

            delete_responses = api.multi_request(delete_commands)
            for response in delete_responses:
                if not response.success:
                    logger.debug(response.notifications)
        except HTTPError as e:
            logger.error("HTTP error syncing relations to Conscribo: %s", e)
        except ResultException as e:
            logger.error("Server error syncing relations to Conscribo: %s", e)
