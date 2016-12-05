import json
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils import translation

import pizzas.models as pizzas_models
import events.models as events_models
import members.models as members_models


def naive_to_aware(date_string):
    """Convert string of form '%Y-%m-%d %H:%M:%S'
    to timezone aware datetime object"""

    naive_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return timezone.get_current_timezone().localize(naive_datetime)


class Command(BaseCommand):
    help = 'Migrate the pizzas from the old website.'

    def handle(self, *args, **options):
        translation.activate('nl')

        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured('MIGRATION_KEY not specified')

        events_api_url = 'https://thalia.nu/pizzas/api/?apikey={}'.format(
            settings.MIGRATION_KEY)

        print('[*]Getting events json data')
        try:
            response = requests.get(events_api_url,
                                    headers={'User-Agent': 'Trumpery'})

        except requests.RequestException:
            print('[!]Could not get {}'.format(events_api_url))
            return

        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print('[!]No json data found')
            return

        activity_map = {}
        product_map = {}

        print('[*]Parsing pizza events.')
        for event_data in data['events']:
            event_date = naive_to_aware(event_data['order_to'])
            events = events_models.Event.objects.filter(
                start__year=event_date.year,
                start__month=event_date.month,
                start__day=event_date.day
            )

            if len(events) == 1:
                event = events.first()
            else:
                for e in events:
                    if 'borrel' in e.title_nl or 'Programmeerwedstrijd'\
                            in e.title_nl:
                        event = e

            new_event = pizzas_models.PizzaEvent(
                event=event,
                start=naive_to_aware(event_data['order_from']),
                end=naive_to_aware(event_data['order_to']),
            )
            new_event.save()
            activity_map[event_data['id']] = new_event.pk

        print('[*]Parsing pizza products.')
        for pizza_data in data['products']:
            new_pizza = pizzas_models.Product(
                name=pizza_data['name'],
                description_nl=pizza_data['description'],
                description_en=pizza_data['description'],
                price=pizza_data['price'],
                available=pizza_data['available']
            )
            new_pizza.save()
            product_map[pizza_data['id']] = new_pizza.pk

        print('[*]Parsing pizza orders.')
        for order_data in data['orders']:
            if order_data['username'] is None:
                member = None
            else:
                registration_user = User.objects.get(
                    username=order_data['username']
                )
                member = members_models.Member.objects.get(
                    user=registration_user
                )
            new_order = pizzas_models.Order(
                member=member,
                paid=order_data['paid'],
                name=order_data['name'],
                product=pizzas_models.Product.objects.get(
                    pk=product_map[order_data['product_id']]
                ),
                pizza_event=pizzas_models.PizzaEvent.objects.get(
                    pk=activity_map[order_data['activity_id']]
                )
            )
            new_order.save()
