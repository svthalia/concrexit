import requests
import re
from bs4 import BeautifulSoup

from datetime import datetime
from django.core.management.base import BaseCommand
from newsletters.models import Newsletter, NewsletterItem, NewsletterEvent


class Command(BaseCommand):
    help = 'Scrapes the newsletters from the old Thalia website'

    def handle(self, *args, **options):
        year_range = range(2015, 2017)
        week_range = range(1, 53)
        url = "https://thalia.nu/nieuwsbrief/{}/{:02d}/nieuwsbrief.html"

        NewsletterItem.objects.all().delete()
        NewsletterEvent.objects.all().delete()
        Newsletter.objects.all().delete()

        session = requests.Session()

        for year in year_range:
            for week in week_range:
                request = session.get(url.format(year, week))
                src= request.text

                if request.status_code != 200:
                    continue

                soup = BeautifulSoup(src, "lxml")

                newsletter = Newsletter()
                title = "Newsletter week {} {}".format(week, year)
                newsletter.title_nl = title
                newsletter.title_en = title
                newsletter.date = datetime.strptime(
                    '{}-W{}-0'.format(year, week - 1),
                    "%Y-W%W-%w").date()

                all_tr = soup.find("table").find_all("tr")

                desc_contents = all_tr[2].find("td").contents
                desc_td = "".join([str(x) for x in desc_contents])

                newsletter.description_nl = desc_td
                newsletter.description_en = desc_td

                newsletter.sent = True

                newsletter.save()

                start = 6 if "AGENDA" in all_tr[3].text else 5

                items = all_tr[start:len(all_tr)]

                for index in range(int((len(items) - 2) / 2)):
                    first_index = index * 2
                    second_index = first_index + 1

                    title_el = items[first_index].find("td").find("h2")

                    title = title_el.text

                    content_tr = items[second_index]
                    content_td = content_tr.find_all("td")

                    description = "".join([str(x) for x in
                                           content_td[0].contents])

                    item = None
                    if len(content_td) > 1:
                        item = NewsletterEvent()

                        event_data = content_td[1].find_all("span")
                        what = event_data[0].text
                        where = event_data[1].text
                        when = event_data[2]

                        price = None
                        if ("PRIJS" in content_td[1].text and
                                event_data[3] is not None):
                            price = event_data[3].text

                        item.what_nl = what[:len(what) - 1]
                        item.what_en = what[:len(what) - 1]
                        item.where_nl = where[:len(where) - 1]
                        item.where_en = where[:len(where) - 1]

                        item.start_datetime = datetime.now()
                        item.end_datetime = datetime.now()

                        if price is not None and "ratis" not in price:
                            price = price.replace(",", ".")
                            price = price.replace("-", "0")
                            if "\x82" in price:
                                price = price[3:len(price) - 1]
                            elif "euro" in price:
                                price = price[0:len(price) - 1]
                                price = price.replace("euro", "")
                            else:
                                price = price[1:len(price) - 1]
                            item.price = float(price)

                        costs = re.findall("Deze bedragen <b>€([0-9]*,"
                                           "[0-9]*)\.</b>", description)
                        if len(costs) > 0:
                            item.penalty_costs = float(
                                costs[0][:len(costs[0]) - 1]
                                .replace(",", ".")
                                .replace("-", "0"))
                        elif item.price is not None:
                            item.penalty_costs = item.price

                        pass
                    else:
                        item = NewsletterItem()

                    item.title_nl = title.lower().capitalize()
                    item.title_en = title.lower().capitalize()
                    item.description_nl = description
                    item.description_en = description
                    item.newsletter = newsletter

                    item.save()
