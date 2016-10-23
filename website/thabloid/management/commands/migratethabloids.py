from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from thabloid.models import Thabloid

from bs4 import BeautifulSoup
import requests
import os


def file_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(BaseCommand):
    help = "Migrates Thabloids"

    def handle(self, *args, **options):
        print("Querying concrete5 for PDFs..")
        url = "https://thalia.nu/index.php/association/thabloid"
        soup = BeautifulSoup(requests.get(url).text, 'lxml')

        for a in soup.find_all('a', {"class": "overlay-icon-link"}):
            pdf_url = "https://thalia.nu" + a['href']
            filename = os.path.basename(pdf_url)
            year, thabloid, issue = os.path.splitext(filename)[0].split('-')
            year = int(year[:2])
            if year >= 90:
                year += 1900
            else:
                year += 2000
            if Thabloid.objects.filter(year=year, issue=int(issue)).exists():
                print("Thabloid {} #{} already exists.. skipping."
                      .format(year, issue))
                continue
            thabloid = Thabloid(year=year, issue=int(issue))
            file_from_url(thabloid.file, pdf_url)
            thabloid.save()
