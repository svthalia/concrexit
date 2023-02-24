from django.core.management.base import BaseCommand

from moneybirdsynchronization.administration import HttpsAdministration
from moneybirdsynchronization.models import Contact
from thaliawebsite import settings
from members.models import Member
from django.db.models import Q, Subquery, OuterRef

class Command(BaseCommand):
    """This command can be executed periodically to sync the contacts with MoneyBird."""

    def handle(self, *args, **options):
        members_without_contact = Member.objects.filter(~Q(id__in=Subquery(Contact.objects.filter(member=OuterRef('pk')).values('member'))))

        for member in members_without_contact:
            contact = Contact(member=member)
            contact.save()

        api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)

        # fetch contact ids from moneybird
        api_response = api.get("contacts")

        # fetch contact ids from contact model
        contact_info = [contact.get_moneybird_info() for contact in Contact.objects.all()]
        
        # find contacts in contact model that are not in moneybird and add to moneybird
        moneybird_ids = [int(info["id"]) for info in api_response]
        for contact in contact_info:
            if contact["id"] is None or int(contact["id"]) not in moneybird_ids:
                contact = Contact.objects.get(member=Member.objects.get(pk=contact["pk"]))
                response = api.post("contacts", contact.to_moneybird())
                contact.moneybird_id = response["id"]
                contact.moneybird_version = response["version"]
                contact.save()
        
        moneybird_info = []
        for contact in api_response:
            if len(contact["custom_fields"]) > 0:
                moneybird_info.append({"id": contact["id"], "version": contact["version"], "pk": contact["custom_fields"][0]["value"]})

        ids = [info["id"] for info in contact_info]
        for moneybird in moneybird_info:
            if int(moneybird["id"]) not in ids:
                response = api.delete("contacts/{}".format(moneybird["id"]))
