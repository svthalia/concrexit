from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from committees.models import Board, Committee
from members.models import Member

from bs4 import BeautifulSoup
import requests
import json
import os


def imagefield_from_url(imagefield, url):
    file = ContentFile(requests.get(url).content)
    imagefield.save(os.path.basename(url), file)


class Command(BaseCommand):
    help = "Migrates members and related committees / memberships"

    def handle(self, *args, **options):
        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured("MIGRATION_KEY not specified")
        url = "https://thalia.nu/api/members_export.php?apikey={}".format(
            settings.MIGRATION_KEY
        )
        data = json.loads(requests.get(url).text)

        board_url = "https://thalia.nu/board/2015-2016"
        soup = BeautifulSoup(requests.get(board_url).text, 'lxml')
        default_board_photo = ("https://thalia.nu/application/files/"
                               "6614/3560/3446/site_logo_board.png")
        for board in data['boards']:
            obj, cr = Board.objects.get_or_create(name=board['name'])
            img = soup.find("img", {"alt": board['name'][8:]})
            if img:
                imagefield_from_url(obj.photo, img['src'])
            else:
                imagefield_from_url(obj.photo, default_board_photo)

        committee_url = "https://thalia.nu/committees"
        soup = BeautifulSoup(requests.get(committee_url).text, 'lxml')
        anchors = soup.find('ul', {'class': 'row committees'}).find_all('a')
        links = {anchor.find('h2').text: anchor['href'] for anchor in anchors}
        for committee in data['committees']:
            obj, cr = Committee.objects.get_or_create(name=committee['name'])
            if committee['name'] not in links:
                continue
            src = requests.get(links[committee['name']]).text
            soup = BeautifulSoup(src, 'lxml')
            div = soup.find('div', {'id': 'committee-div'})
            obj.description = div.find('p').text
            img = div.find('img')
            imagefield_from_url(obj.photo, "https://thalia.nu" + img['src'])

        for member in data['members']:
            user, cr = User.objects.get_or_create(username=member['username'])
            user.username = member['username']
            user.email = member['email']
            # Concrete5 uses bcrypt passwords, which django can rehash
            user.password = 'bcrypt$' + member['password']
            user.first_name = member['first_name']
            user.last_name = member['surname']
            user.save()
            if not user.member:
                user.member = Member()
            user.member.programme = {
                'Computer Science': 'computingsience',
                'Information Science': 'informationscience',
                'Other': None,
            }[member['study']]
            if member['student_number']:
                user.member.student_number = member['student_number']
            if member['member_since']:
                # This is as best as we can do, although this may be incorrect
                user.member.starting_year = member['member_since']
            user.member.address_street = member['address1']
            if member['address2']:
                user.member.address_street2 = member['address2']
            user.member.address_city = member['city']
            user.member.address_postal_code = member['postalcode']
            if member['mobile_number']:
                user.member.phone_number = member['mobile_number']
            elif member['phone_number']:
                user.member.phone_number = member['phone_number']
            if member['phone_number_parents']:
                user.member.emergency_contact = '[default: Parents]'
                user.member.emergency_contact_phone_number = (
                    member['phone_number_parents'])
            if member['birthday']:
                user.member.birthday = member['birthday'].split(' ')[0]
            user.member.show_birthday = bool(member['show_birthday'])
            if member['website']:
                user.member.website = member['website']
            if member['about']:
                user.member.profile_description = member['about']
            if member['nickname']:
                user.member.nickname = member['nickname']
            if member['initials']:
                user.member.initials = member['initials']
            user.member.display_name_preference = {
                'Full name': 'full',
                'Initials and last name': 'initials',
                'First name': 'full',
                'Nickname': 'nickname',
                'First name + nickname + last name': 'fullnick',
                'Nickname + last name': 'nicklast',
            }[member['display_name']]
            if member['avatar']:
                imagefield_from_url(user.member.photo, member['avatar'])
            if member['language']:
                user.member.language = member['language']
            user.member.receive_optin = member['receive_optin_mail']
            user.member.direct_debit_authorized = (
                member['payment_authorised'] == 'Authorised')
            if member['payment_iban']:
                user.member.bank_account = member['payment_iban']

            # TODO link member to committees through memberships
            # TODO administrate roles / presidencies
