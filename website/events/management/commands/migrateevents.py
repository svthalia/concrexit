from django.utils import timezone
from django.utils.timezone import datetime

from utils.management.commands import legacylogin
from events.models import Event

from bs4 import BeautifulSoup
import requests
import os
import re

class Command(legacylogin.Command):
    help = "Scrapes the events from the old Thalia website"


    def handle(self, *args, **options):
        super().handle(*args, **options)

        if Event.objects.count() != 0:
            print("This command should only be executed when there are no events yet.")
            return

        url = "https://thalia.nu/events/admin/activity"
        documentpage = self.session.get(url)
        soup = BeautifulSoup(documentpage.text, 'lxml')

        for form in soup.find_all('form'):
            eventid = int(form.input['value'])

            eventurl = "https://thalia.nu/events/admin/activity/edit/{}".format(eventid)
            soup = BeautifulSoup(self.session.get(eventurl).text, 'lxml')
            event = Event()
            event.id = eventid

            event.title = soup.find(id='title')['value']
            event.description = soup.find(id='description').text

            times = [int(el['value']) for el in soup.find_all(selected=True)]

            # TODO: Make this better!
            dates = {}

            for date_type in ('begin_registration_dt',
                              'end_registration_dt',
                              'end_date_dt',
                              'start_date_dt',
                              'end_cancel_dt'):

                script_tag = soup.find('script', text=lambda match: date_type in match)

                if script_tag:
                    # TODO: Please dont hate me for this regex
                    match = re.search(r'{}[\s\S]+new Date\((\d{{4}}), (\d{{1,2}}) - 1, (\d{{1,2}})\)\)'.format(date_type), script_tag.text)

                    year = match.group(1)
                    month = match.group(2)
                    day = match.group(3)

                    dates[date_type] = '{}-{}-{}'.format(year, month, day)

            event.start = '{} {}:{}'.format(dates['start_date_dt'], times.pop(0), times.pop(0))
            event.end = '{} {}:{}'.format(dates['end_date_dt'], times.pop(0), times.pop(0))
            event.registration_start = '{} {}:{}'.format(dates['begin_registration_dt'], times.pop(0), times.pop(0))
            event.registration_end = '{} {}:{}'.format(dates[''], times.pop(0), times.pop(0))
            canceldate = soup.find(id='end_cancel_dt')
            event.cancel_deadline = '{} {}:{}'.format(canceldate, times.pop(0), times.pop(0))

            event.location = soup.find(id='location')['value']
            event.price = float(soup.find(id='member_price')['value'])
            event.cost = float(soup.find(id='thalia_costs')['value'])
            event.max_participants = int(soup.find(id='registration_limit')['value'])
            event.published = form.a.span.text == 'Ja'
            event.save()
