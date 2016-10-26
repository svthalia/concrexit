import json
import os
from datetime import datetime

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from partners.models import (
    Partner,
    PartnerImage,
    VacancyCategory,
    Vacancy,
    PartnerEvent,
)


def naive_to_aware(date_string):
    """Convert string of form '%Y-%m-%d %H:%M:%S'
    to timezone aware datetime object"""

    naive_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return timezone.get_current_timezone().localize(naive_datetime)


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(BaseCommand):
    help = 'Migrate the partners from the old website.'

    def handle(self, *args, **options):

        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured('MIGRATION_KEY not specified')

        url = 'https://thalia.nu/sponsor/api/?apikey={}'.format(
            settings.MIGRATION_KEY)

        input_val = input(
            'Do you want to delete all existing objects? (type yes or no) ')
        if input_val == 'yes':
            Vacancy.objects.all().delete()
            VacancyCategory.objects.all().delete()
            PartnerEvent.objects.all().delete()
            PartnerImage.objects.all().delete()
            Partner.objects.all().delete()

        session = requests.Session()
        src = session.get(url).text

        if 'invalid api key' in src:
            raise PermissionDenied('Invalid API key')

        data = json.loads(src)

        partner_map = {}

        print('Importing partners')
        for src in data['sponsors']:
            partner = Partner()
            partner.name = src['name']
            partner.slug = src['slug']
            partner.is_active = src['is_active']
            partner.is_main_partner = src['is_main_sponsor']
            partner.company_profile = src['company_profile']
            partner.address = src['address']
            partner.zip_code = src['zip_code']
            partner.city = src['city']
            filefield_from_url(partner.logo, src['logo'])
            partner.save()

            for image in src['images']:
                partner_image = PartnerImage()
                partner_image.partner = partner
                filefield_from_url(partner_image.image, image)
                partner_image.save()

            partner_map[src['id']] = partner.pk

        print('Importing partner events')
        for src in data['events']:
            event = PartnerEvent()
            event.title_nl = src['title']
            event.title_en = src['title']
            event.description_nl = src['description']
            event.description_en = src['description']
            location = src['location'] if src['location'] is not None else ""
            event.location_nl = location
            event.location_en = location
            event.start = naive_to_aware(src['start_date'])
            event.end = naive_to_aware(src['end_date'])
            event.url = src['link']
            event.published = True
            event.partner_id = partner_map[src['sponsor_id']]
            event.save()

        category_map = {}

        print('Importing vacancy categories')
        for src in data['categories']:
            category = VacancyCategory()
            category.name_nl = src['name']
            category.name_en = src['name']
            category.slug = src['slug']
            category.save()

            category_map[src['id']] = category.pk

        print('Importing vacancies')
        for src in data['vacancies']:
            vacancy = Vacancy()
            vacancy.title = src['title']
            vacancy.description = src['description']
            vacancy.link = src['link']

            if src['sponsor_id'] is not None:
                vacancy.partner_id = partner_map[src['sponsor_id']]
            else:
                vacancy.company_name = src['company_name']
                filefield_from_url(vacancy.company_logo, src['logo'])

            vacancy.save()

            for id in src['categories']:
                vacancy.categories.add(VacancyCategory.objects
                                       .get(pk=category_map[id]))
