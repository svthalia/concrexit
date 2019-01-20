import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.defaultfilters import date
from requests import HTTPError

from members.models import Member
from utils.conscribo.api import ConscriboApi, ResultException
from utils.conscribo.objects import Command as ApiCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run instead of syncing for real',
        )

    def handle(self, *args, **options):
        api = ConscriboApi(settings.CONSCRIBO_ACCOUNT,
                           settings.CONSCRIBO_USER,
                           settings.CONSCRIBO_PASSWORD)

        try:
            relations_response = api.single_request(
                'listRelations',
                entityType='lid',
                requestedFields={
                    'fieldName': ['website_id', 'code']
                },
            )
            relations_response.raise_for_status()
            relations_response = relations_response.data

            current_relations = {}
            if len(relations_response.get('relations')) > 0:
                current_relations = {
                    int(r.get('website_id')): r.get('code', None)
                    for r in relations_response.get('relations').values()
                }

            replace_commands = []
            for member in Member.current_members.all():
                code = current_relations.pop(member.pk, None)
                profile = member.profile

                fields = {
                    'website_id': member.pk,
                    'voornaam': member.first_name,
                    'naam': member.last_name,
                    'einddatum_lidmaatschap':
                        date(member.current_membership.until, 'Y-m-d'),
                    'e_mailadres': member.email,
                    'straatnaam': profile.address_street,
                    'postcode': profile.address_postal_code,
                    'plaats': profile.address_city,
                    'land': 'Nederland',
                    'bankrekeningnummer': {
                        'name': '',
                        'bic': '',
                        'iban': profile.bank_account,
                    },
                }

                replace_commands.append(ApiCommand(
                    command='ReplaceRelation',
                    entityType='lid',
                    fields=fields,
                    code=code,
                ))

            delete_commands = []
            for website_id, code in current_relations.items():
                delete_commands.append(ApiCommand(
                    command='DeleteRelation',
                    entityType='lid',
                    code=code,
                    website_id=website_id  # not used by server
                ))

            delete_responses = api.multi_request(delete_commands)
            for response in delete_responses:
                if not response.success:
                    logger.debug(response.notifications)
                    website_id = delete_commands[
                        response.request_sequence].data.get('website_id')
                    code = delete_commands[
                        response.request_sequence].data.get('code')
                    member = Member.objects.get(pk=website_id)

                    fields = {
                        'website_id': member.pk,
                        'voornaam': member.first_name,
                        'naam': member.last_name,
                        'einddatum_lidmaatschap':
                            date(member.latest_membership.until, 'Y-m-d'),
                        'e_mailadres': '',
                        'straatnaam': '',
                        'postcode': '',
                        'plaats': '',
                        'land': '',
                        'bankrekeningnummer': {
                            'name': '',
                            'bic': '',
                            'iban': '',
                        },
                    }

                    replace_commands.append(ApiCommand(
                        command='ReplaceRelation',
                        entityType='lid',
                        fields=fields,
                        code=code,
                    ))

            replace_responses = api.multi_request(replace_commands)
            for response in replace_responses:
                if not response.success:
                    logger.debug(response.notifications)
        except HTTPError as e:
            logger.error('HTTP error syncing relations to Conscribo', e)
        except ResultException as e:
            logger.error('Server error syncing relations to Conscribo', e)
