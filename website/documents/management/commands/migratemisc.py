import os

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from documents.models import MiscellaneousDocument
from utils.management.commands import legacylogin


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(legacylogin.Command):
    help = "Scrapes the Miscellaneous Documents from the old Thalia website"

    def handle(self, *args, **options):
        super().handle(*args, **options)
        url = "https://thalia.nu/association/documents"
        documentpage = self.session.get(url)
        soup = BeautifulSoup(documentpage.text, 'lxml')
        container = soup(attrs={'class': 'generalcontainer'})[0]
        documents = container.find_all('li', recursive=False)
        for document in documents:
            name = document.find('h2').find(text=True)
            obj, cr = MiscellaneousDocument.objects.get_or_create(name=name)
            url = document.find(attrs={'class': 'overlay-icon-link'})
            if url is not None:
                url = "https://thalia.nu" + url['href']
                filefield_from_url(obj.file, url)
