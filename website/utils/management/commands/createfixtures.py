import random
import string
import tempfile

from django.contrib.auth.models import User

from django.core.management.base import BaseCommand

from django.core.files import File

from members.models import Member, Membership
from utils import identicon

import factory
from faker import Factory as FakerFactory
faker = FakerFactory.create('nl_NL')


class MemberFactory(factory.Factory):
    class Meta:
        model = Member

    programme = random.choice(['computingscience', 'informationscience'])
    student_number = factory.LazyAttribute(
        lambda x: faker.numerify(text="s#######"))
    starting_year = 2016

    address_street = factory.LazyAttribute(lambda x: faker.street_address())
    address_postal_code = factory.LazyAttribute(lambda x: faker.postcode())
    address_city = factory.LazyAttribute(lambda x: faker.city())

    phone_number = '+31' + faker.numerify(text="##########")


class Command(BaseCommand):
    help = "Creates fake data to test the site with"

    def add_arguments(self, parser):
        parser.add_argument(
            "-u", "--user", type=int, help="The amount of fake users to add")

    def handle(self, **options):
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
                    user.last_name = fakeprofile['name'].split()[1]

                    member = MemberFactory()
                    member.user_id = user.id
                    member.birthday = fakeprofile['birthdate']
                    member.website = fakeprofile['website'][0]

                    code = sum([ord(x) for x in fakeprofile['username']])
                    icon = identicon.render_identicon(code, 50)
                    with tempfile.TemporaryFile() as tfile:
                        icon.save(tfile, 'PNG')
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
