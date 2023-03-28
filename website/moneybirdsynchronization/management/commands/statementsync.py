from django.core.management.base import BaseCommand
import datetime
from moneybirdsynchronization import services
from payments.models import Payment
from moneybirdsynchronization.administration import HttpsAdministration
from thaliawebsite import settings

class Command(BaseCommand):
    """This command needs to be executed every day to sync the bookkeeping with MoneyBird."""

    def handle(self, *args, **options):

        payment_identifiers = {
            Payment.TPAY: "ThaliaPay",
            Payment.CASH: "cashtanje",
            Payment.CARD: "pin"
        }
        
        date = datetime.date.today()
        new_card_payments = Payment.objects.filter(type=Payment.CARD, created_at__year=date.year, created_at__month=date.month, created_at__day=date.day, moneybird_financial_statement_id=None)
        new_cash_payments = Payment.objects.filter(type=Payment.CASH, created_at__year=date.year, created_at__month=date.month, created_at__day=date.day, moneybird_financial_statement_id=None)
        
        api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)

        card_account_id = services.get_financial_account_id(api, payment_identifiers[Payment.CARD])
        services.link_transaction_to_financial_account(api, card_account_id, new_card_payments)

        cash_account_id = services.get_financial_account_id(api, payment_identifiers[Payment.CASH])
        services.link_transaction_to_financial_account(api, cash_account_id, new_cash_payments)

        