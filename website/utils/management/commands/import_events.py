import os
import sys
import re
import json
import requests
import events.models as events_models

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

        event_fields_translations = {

            # name in data : name in model
            'id': 'id',
            'title': 'title',
            'description': 'description',
            'location': 'location',
            'start_date': 'start',
            'end_date': 'end',
            'member_price': 'price',
            'thalia_costs': 'cost',
            'registration_limit': 'max_participants',
            'public': 'published',
            'begin_registration': 'registration_start',
            'end_registration': 'registration_end',
            'end_cancel': 'cancel_deadline',
            'registration_not_needed_message': 'no_registration_message',
        }

        # Not in data: map_location, organiser
        # In data but not Model: needs_registration

        # Event
        for event_data in data['events']:

            new_event = events_models.Event()

            for concrete_field in event_fields_translations:

                django_field = event_fields_translations[concrete_field]

                concrete_data = event_data[concrete_field]

                # MultilingualField
                if django_field in ('title', 'description', 'location', 'no_registration_message'):
                    for language_code in ('en', 'nl'):
                        django_multilangiualfield = '{}_{}'.format(django_field, language_code)

                        if not hasattr(new_event, django_multilangiualfield):
                            print('[!]Could neither find {} nor {}'.format(django_field, django_multilangiualfield))
                            return

                        setattr(new_event, django_multilangiualfield, concrete_data)

                # DateTimeField
                elif django_field in ('start', 'end', 'begin_registration', 'end_registration', 'end_cancel'):
                    setattr(new_event, django_field, datetime.strptime(concrete_data, '%Y-%m-%d %H:%M:%S'))

                # DecimalField
                elif django_field in ('price', 'cost'):

                    if re.match(r'[-+]?\d*\.?\d+$', concrete_data):
                        setattr(new_event, django_field, float(concrete_data))
                    else:
                        setattr(new_event, django_field, 0)

                # PositiveSmallIntegerField
                elif django_field == 'registration_limit':
                    setattr(new_event, django_field, int(concrete_data))

                elif django_field == 'published':
                    setattr(new_event, django_field, bool(int(concrete_data)))

            # TODO: new_event.save()

        # RegistrationInformationField
        # TODO: RegistrationInformationField and MultiLingualField
        for field_data in data['extra_fields']:

            new_registration_information_field = events_models.RegistrationInformationField()

            event_id = field_data['activity_id']

            new_registration_information_field.event = events_models.Event().get(id=event_id)

            data_types = {
                '0': 'charfield',
                '1': 'intfield',
                '2': 'checkbox',
            }
            new_registration_information_field.type = data_types[field_data['data_type']]

            new_registration_information_field.name = field_data['field_name']
            new_registration_information_field.description = field_data['field_explanation']


        # Registration
        # for event_data in data['registrations']
