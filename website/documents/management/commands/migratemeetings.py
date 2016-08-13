from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.timezone import datetime

from utils.management.commands import legacylogin
from documents.models import GeneralMeeting, GeneralMeetingDocument

from bs4 import BeautifulSoup
import requests
import os


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(legacylogin.Command):
    help = "Scrapes the General Meetings from the old Thalia website"

    def handle(self, *args, **options):
        super().handle(*args, **options)
        url = "https://thalia.nu/ajax/alvyearview?year={}"
        for year in range(1990, 2016):
            src = self.session.get(url.format(year)).text
            soup = BeautifulSoup(src, 'lxml')
            for alv in soup.div.find_all('div', recursive=False):
                meeting = GeneralMeeting()
                datetext = alv.find(attrs={'class': 'gw-go-coinb'}).text
                date = datetime.strptime(datetext.strip() + ' ' + str(year),
                                         '%d %b %Y')
                if date.month < 9:
                    date = datetime(year+1, date.month, date.day)
                date = timezone.make_aware(date,
                                           timezone.get_current_timezone())
                meeting.datetime = date
                meeting.location = alv.find('p').text
                meeting.save()
                minutes = alv.find('div', {'class': 'gw-go-footer'}).find('a')
                if minutes is not None:
                    minutes_url = 'https://thalia.nu' + minutes['href']
                    filefield_from_url(meeting.minutes, minutes_url)
                for document in alv.find_all('li'):
                    doc_url = 'https://thalia.nu' + document.find('a')['href']
                    doc = GeneralMeetingDocument()
                    doc.meeting = meeting
                    filefield_from_url(doc.file, doc_url)
                    doc.save()
