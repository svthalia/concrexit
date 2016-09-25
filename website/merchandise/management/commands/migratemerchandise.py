from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from decimal import Decimal

from merchandise.models import MerchandiseItem

from bs4 import BeautifulSoup
import requests
import os


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(BaseCommand):
    help = "Scrapes the merchandise from the old Thalia website"

    def handle(self, *args, **options):
        input_val = input(
            "Do you want to delete all existing objects? (type yes or no) ")
        if input_val == 'yes':
            MerchandiseItem.objects.all().delete()

        session = requests.Session()
        url = "https://thalia.nu/index.php/association/merchandise"
        src = session.get(url).text
        soup = BeautifulSoup(src, 'lxml')
        for item in soup.find_all("div", {"class": "post", "id": "item"}):
            image_url = item.find("img")['src'].replace('/small', '/large')
            title = item.find("h1", {"id": "merchandise-title"}).text
            desc = item.find("p", {"id": "merchandise-desc"}).text
            price = Decimal(item.find("div", {"id": "merchandise-price"})
                            .text[9:].replace(',', '.'))

            print("Importing {}".format(title))

            merch = MerchandiseItem()
            merch.name_nl = title
            merch.name_en = title
            merch.description_nl = desc
            merch.description_en = desc
            merch.price = price
            filefield_from_url(merch.image, image_url)
            merch.save()
