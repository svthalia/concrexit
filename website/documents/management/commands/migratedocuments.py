import os

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.timezone import datetime

from documents.models import (AssociationDocumentsYear, GeneralMeeting,
                              GeneralMeetingDocument, MiscellaneousDocument)
from utils.management.commands import legacylogin


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(legacylogin.Command):
    help = "Scrapes the documents from the old Thalia website"

    def handle(self, *args, **options):
        super().handle(*args, **options)

        print("Migrating the general meetings")
        url = "https://thalia.nu/ajax/alvyearview?year={}"
        for year in range(1990, 2017):
            print("Migrating {}".format(year))
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
        print("Migrating general meetings complete")

        print("Migrating the policy documents")
        url = "https://thalia.nu/association/documents"
        documentpage = self.session.get(url)
        soup = BeautifulSoup(documentpage.text, 'lxml')
        wrapper = soup(attrs={'class': 'policywrapper'})[0]
        uls = wrapper.find_all('ul', recursive=False)
        policies = uls[0].find_all('li', recursive=False)
        reports = uls[1].find_all('li', recursive=False)
        for policy, report in zip(policies, reports):
            year = policy.find('h2').find(text=True)
            print("Migrating {}".format(year))
            year = int(year.replace("Beleidsplan '", '')[:2])
            year += (19 if year >= 90 else 20) * 100
            obj, cr = AssociationDocumentsYear.objects.get_or_create(year=year)
            obj.year = year
            files = [(obj.policy_document,
                      policy.find(attrs={'class': 'overlay-icon-link'})),
                     (obj.annual_report,
                      report.find(attrs={'class': 'overlay-icon-link'})),
                     (obj.financial_report,
                      report.find(attrs={'class': 'overlay-icon-euro'}))]
            for filefield, url in files:
                if url is not None:
                    url = "https://thalia.nu" + url['href']
                    file = ContentFile(requests.get(url).content)
                    # File names are ignored when serving files anyway
                    filefield.save(os.path.basename(url), file)
        print("Migrating policy documents complete")

        print("Migrating the miscellaneous documents")
        container = soup(attrs={'class': 'generalcontainer'})[0]
        documents = container.find_all('li', recursive=False)
        for document in documents:
            name = document.find('h2').find(text=True)
            print("Migrating {}".format(name))
            obj, cr = MiscellaneousDocument.objects.get_or_create(name=name)
            url = document.find(attrs={'class': 'overlay-icon-link'})
            if url is not None:
                url = "https://thalia.nu" + url['href']
                filefield_from_url(obj.file, url)
        print("Migrating miscellaneous documents complete")
