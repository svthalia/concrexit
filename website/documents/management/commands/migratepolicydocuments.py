from django.core.files.base import ContentFile

from utils.management.commands import legacylogin
from documents.models import AssociationDocumentsYear

from bs4 import BeautifulSoup
import requests
import os


class Command(legacylogin.Command):
    help = "Scrapes the policy documents from the old Thalia website"

    def handle(self, *args, **options):
        super().handle(*args, **options)
        url = "https://thalia.nu/association/documents"
        documentpage = self.session.get(url)
        soup = BeautifulSoup(documentpage.text, 'lxml')
        wrapper = soup(attrs={'class': 'policywrapper'})[0]
        uls = wrapper.find_all('ul', recursive=False)
        policies = uls[0].find_all('li', recursive=False)
        reports = uls[1].find_all('li', recursive=False)
        for policy, report in zip(policies, reports):
            year = policy.find('h2').find(text=True)
            year = int(year.replace("Beleidsplan '", '')[:2])
            year = (19 if year >= 90 else 20)*100 + year
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
