import os
import sys
import json
import requests
import events.models as events_models

from django.conf import settings
from datetime import datetime
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Make the events database great.'

    def handle(self, *args, **options):

        api_key = 'fcd7ad95a6ae9d70bc844e0f3dcd9b6518c7dd78'
        events_api_url = 'https://thalia.nu/events/api/?apikey={}'.format(api_key)

        print('[*]Getting events json data')
        try:

            response = requests.get(events_api_url,
                                    timeout=2,
                                    headers={'User-Agent': 'The Donald'})

        except requests.RequestException:
            print('[!]Could not get {}'.format(events_api_url))
            return

        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print('[!]No json data found')
            return

        fields_translations = {

            # name in data : name in model
            'title': 'title',
            'description': 'description',
            'start': '',
            'end': '',


        }

        for concrete_field in fields_translations:
            for event_data in data['events']:
                new_event = events_models.Event()

                django_field = fields_translations[concrete_field]

                if django_field in ('title', 'description'):
                    concrete_data = event_data[concrete_field]

                elif django_field in ('start', 'end'):

                    concrete_data = datetime.strptime(event_data[concrete_field], '')

                if not hasattr(new_event, django_field):
                    for language_code in [language[0] for language in settings.LANGUAGES]:
                        django_multilangiualfield = '{}_{}'.format(django_field, language_code)

                        if not hasattr(new_event, django_multilangiualfield):
                            print('[!]Could neither find {} nor {}'.format(django_field, django_multilangiualfield))
                            return

                        setattr(new_event, django_multilangiualfield, concrete_data)
                else:
                    setattr(new_event, django_field, concrete_data)





