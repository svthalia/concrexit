import random
import string
import tempfile
from datetime import date

import factory
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from faker import Factory as FakerFactory

from members.models import Member, Membership
from partners.models import Partner
from pydenticon import Generator as IconGenerator

faker = FakerFactory.create('nl_NL')


class MemberFactory(factory.Factory):
    class Meta:
        model = Member

    programme = random.choice(['computingscience', 'informationscience'])
    student_number = factory.LazyAttribute(
        lambda x: faker.numerify(text="s#######"))
    starting_year = random.randint(1990, date.today().year)

    address_street = factory.LazyAttribute(lambda x: faker.street_address())
    address_postal_code = factory.LazyAttribute(lambda x: faker.postcode())
    address_city = factory.LazyAttribute(lambda x: faker.city())

    phone_number = '+31' + faker.numerify(text="##########")


class Command(BaseCommand):
    help = "Creates fake data to test the site with"

    def add_arguments(self, parser):
        parser.add_argument(
            "-u", "--user", type=int, help="The amount of fake users to add")
        parser.add_argument(
            "-p",
            "--partner",
            type=int,
            help="The amount of fake partners to add")

    def create_partner(self, partner):
        partner.name = faker.company() + ' ' + faker.company_suffix()
        partner.slug = faker.slug()
        partner.link = faker.uri()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(partner.name, 480, 480, (
            10, 10, 10,
            10))  # 620x620 pixels, with 10 pixels padding on each side
        with tempfile.TemporaryFile() as tfile:
            tfile.write(icon)
            partner.logo.save(partner.name + '.png', File(tfile))

        partner.address = faker.street_address()
        partner.zip_code = faker.postcode()
        partner.city = faker.city()

    def handle(self, **options):
        if not (options['user'] and options['partner']):
            print("Use ./manage.py help createfixtures to find out how to call"
                  " this command")
        if options['user']:
            print("Creating fake profiles for", options['user'], "users.")

            for __ in range(options['user']):
                try:
                    fakeprofile = faker.profile()
                    fakeprofile['password'] = ''.join(
                        random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(16))
                    user = User.objects.create_user(fakeprofile['username'],
                                                    fakeprofile['mail'],
                                                    fakeprofile['password'])
                    user.first_name = fakeprofile['name'].split()[0]
                    user.last_name = ' '.join(fakeprofile['name'].split()[1:])

                    member = MemberFactory()
                    member.user_id = user.id
                    member.birthday = fakeprofile['birthdate']
                    member.website = fakeprofile['website'][0]

                    igen = IconGenerator(5, 5)  # 5x5 blocks
                    icon = igen.generate(user.username, 480, 480, (
                        10, 10, 10, 10
                    ))  # 620x620 pixels, with 10 pixels padding on each side
                    with tempfile.TemporaryFile() as tfile:
                        tfile.write(icon)
                        member.photo.save(fakeprofile['username'] + '.png',
                                          File(tfile))

                    membership = Membership()
                    membership.user_id = user.id
                    membership.since = faker.date_time_between(
                        start_date='-4y', end_date='now', tzinfo=None)
                    membership.until = random.choice([faker.date_time_between(
                        start_date='-2y', end_date='2y', tzinfo=None), None])
                    membership.type = random.choice(
                        ['member', 'supporter', 'honorary'])
                except Exception as e:
                    raise e
                else:
                    user.save()
                    member.save()
                    membership.save()
                    print("Created user with username", user.username)
        if options['partner']:
            print("Creating fake profiles for", options['partner'], "partners")

            try:
                Partner.objects.get(is_main_partner=True)
            except Partner.DoesNotExist:
                partner = Partner()
                partner.is_active = True
                partner.is_main_partner = True

                self.create_partner(partner)

            for __ in range(options['partner']):
                try:
                    partner = Partner()
                    self.create_partner(partner)
                except Exception as e:
                    raise e
                else:
                    partner.save()
