import json
import os

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from django.utils.translation import activate

from activemembers.models import (Board, Committee,
                                  CommitteeMembership, Mentorship)
from members.models import Member, Membership


def imagefield_from_url(imagefield, url):
    file = ContentFile(requests.get(url).content)
    imagefield.save(os.path.basename(url), file)


class Command(BaseCommand):
    help = "Migrates members and related committees / memberships"

    def handle(self, *args, **options):
        activate('en')
        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured("MIGRATION_KEY not specified")
        url = "https://thalia.nu/api/members_export.php?apikey={}".format(
            settings.MIGRATION_KEY
        )
        print("Querying concrete5.. this may take a while")
        data = json.loads(requests.get(url).text)

        groups = {}
        mentorgroups = {}

        board_url = "https://thalia.nu/board/2015-2016"
        soup = BeautifulSoup(requests.get(board_url).text, 'lxml')
        default_board_photo = ("https://thalia.nu/application/files/"
                               "6614/3560/3446/site_logo_board.png")
        print("Migrating boards..")
        for board in data['boards']:
            obj, cr = Board.objects.get_or_create(name_nl=board['name'])
            obj.name_en = board['name']
            print(obj.name_en)
            groups[board['gID']] = obj
            img = soup.find("img", {"alt": board['name'][8:]})
            if img:
                imagefield_from_url(obj.photo, img['src'])
            else:
                imagefield_from_url(obj.photo, default_board_photo)
            obj.save()

        for mentorgroup in data['mentors']:
            mentorgroups[mentorgroup['gID']] = int(mentorgroup['name'][-4:])

        print("Migrating committees..")
        committee_url = "https://thalia.nu/committees"
        soup = BeautifulSoup(requests.get(committee_url).text, 'lxml')
        anchors = soup.find('ul', {'class': 'row committees'}).find_all('a')
        links = {anchor.find('h2').text: anchor['href'] for anchor in anchors}
        for committee in data['committees']:
            obj, cr = Committee.objects.get_or_create(
                name_nl=committee['name'])
            obj.name_en = committee['name']
            print(obj.name_en)
            groups[committee['gID']] = obj
            obj.save()
            if committee['name'] not in links:
                continue
            src = requests.get(links[committee['name']]).text
            soup = BeautifulSoup(src, 'lxml')
            div = soup.find('div', {'id': 'committee-div'})
            obj.description_en = div.find('p').text
            obj.description_nl = div.find('p').text
            img = div.find('img')
            imagefield_from_url(obj.photo, "https://thalia.nu" + img['src'])

        for member in data['members']:
            user, cr = User.objects.get_or_create(username=member['username'])
            print("Migrating {}".format(member['username']))
            user.username = member['username']
            user.email = member['email']
            # Concrete5 uses bcrypt passwords, which django can rehash
            user.password = 'bcrypt$' + member['password']
            user.first_name = member['first_name']
            user.last_name = ' '.join([member['infix'], member['surname']])
            user.save()
            try:
                user.member
            except Member.DoesNotExist:
                user.member = Member()
            user.member.programme = {
                'Computer Science': 'computingsience',
                'Information Science': 'informationscience',
                'Other': None,
                '': None,
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
                if user.member.birthday == "0000-00-00":
                    user.member.birthday = None
                elif user.member.birthday[:3] == "201":  # Likely incorrect!
                    user.member.birthday = None

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
                'First name': 'firstname',
                'Nickname': 'nickname',
                'First name + nickname + last name': 'fullnick',
                'Nickname + last name': 'nicklast',
                '': 'full',
            }[member['display_name']]
            if member['avatar']:
                imagefield_from_url(user.member.photo, member['avatar'])
            if member['language']:
                user.member.language = member['language']
            user.member.receive_optin = bool(member['receive_optin_mail'])
            user.member.direct_debit_authorized = (
                member['payment_authorised'] == 'Authorised')
            if member['payment_iban']:
                user.member.bank_account = member['payment_iban']
            user.member.save()

            membership = Membership()
            membership.user = user
            if member['membership_type'] == 'Benefactor':
                membership.type = 'supporter'
                membership.until = parse_date("2017-09-01")
            if member['membership_type'] == 'Yearly Membership':
                membership.type = 'member'
                membership.until = parse_date("2017-09-01")
            if member['membership_type'] == 'Study Membership':
                membership.type = 'member'
            if member['membership_type'] == 'Honorary Member':
                membership.type = 'honorary'
            membership.save()

            for membership in member['memberships']:
                mdata = membership['membership']
                if not mdata['begindate'] or mdata['begindate'][:4] == '0000':
                    mdata['begindate'] = '1970-01-01'  # Manually fix this
                for p in membership['presidencies'] + membership['roles']:
                    if not p['begindate'] or p['begindate'][:4] == '0000':
                        p['begindate'] = '1970-01-01'

                if mdata['gID'] in mentorgroups:
                    m, cr = Mentorship.objects.get_or_create(
                                year=mentorgroups[mdata['gID']],
                                member=user.member)
                    m.save()
                if mdata['gID'] not in groups:
                    continue  # These are concrete5 groups (Admin, etc..)
                group = groups[mdata['gID']]
                dates = ([p['begindate'] for p in membership['presidencies']] +
                         [p['enddate'] for p in membership['presidencies']] +
                         [r['begindate'] for r in membership['roles']] +
                         [r['enddate'] for r in membership['roles']] +
                         [mdata['begindate']])
                dates = set(dates)
                try:
                    dates.remove(mdata['enddate'])
                    dates.remove(None)
                except KeyError:
                    pass  # Silence if enddate or None do not appear
                if not dates:
                    dates = {'1970-01-01'}  # Manually fix where this appears
                newmship = None
                for date in sorted(dates):
                    if newmship:
                        newmship.until = parse_date(date)
                        newmship.save()
                    newmship = CommitteeMembership()
                    newmship.member = user.member
                    newmship.committee = group
                    newmship.since = parse_date(date)
                    presidencies = [p for p in membership['presidencies']
                                    if p['begindate'] >= date and
                                    (not p['enddate'] or date < p['enddate'])]
                    if len(presidencies) >= 1:
                        newmship.chair = True
                    roles = [r['role'] for r in membership['roles']
                             if r['begindate'] >= date and
                             (not r['enddate'] or date < r['enddate'])]
                    if len(roles) >= 1:
                        newmship.role_nl = ' / '.join(roles)
                        newmship.role_en = ' / '.join(roles)
                if mdata['enddate'] is not None:
                    if newmship.since != parse_date(mdata['enddate']):
                        newmship.until = parse_date(mdata['enddate'])
                        newmship.save()
                else:
                    newmship.save()

            for m in CommitteeMembership.objects.filter(member=user.member):
                ms = (CommitteeMembership.objects
                                         .filter(committee_id=m.committee_id,
                                                 member_id=m.member_id,
                                                 since=m.until,
                                                 chair=m.chair,
                                                 role_en=m.role_en,
                                                 role_nl=m.role_nl,
                                                 ))
                if not ms:
                    continue
                if len(ms) > 1:
                    raise Exception("Could not merge more than one membership")
                m.until = ms[0].until
                m.save()
                ms[0].delete()

        print("Sanitizing board memberships")
        for m in CommitteeMembership.objects.all():
            try:
                if m.committee.board:
                    m.since = parse_date(
                        '{}-09-01'.format(m.committee.name_nl[8:12]))
                    m.until = parse_date(
                        '{}-09-01'.format(m.committee.name_nl[13:17]))
                    m.save()
            except Board.DoesNotExist:
                pass

        # remove duplicates to be sure
        print("Cleaning up duplicates")
        for m in CommitteeMembership.objects.all():
            if (CommitteeMembership.objects
                                   .filter(committee_id=m.committee_id,
                                           member_id=m.member_id,
                                           since=m.since,
                                           chair=m.chair,
                                           role_en=m.role_en,
                                           role_nl=m.role_nl)
                                   .count()) > 1:
                m.delete()
