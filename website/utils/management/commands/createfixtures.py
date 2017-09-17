import math
import random
import string
import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from activemembers.models import Board, Committee, CommitteeMembership
from events.models import Event
from members.models import Member, Membership
from partners.models import Partner, Vacancy, VacancyCategory
from pizzas.models import Product
from utils.snippets import datetime_to_lectureyear

import factory
from faker import Factory as FakerFactory
from pydenticon import Generator as IconGenerator

faker = FakerFactory.create('nl_NL')
pizza_name_faker = FakerFactory.create('it_IT')
current_tz = timezone.get_current_timezone()


def generate_title():
    words = faker.words(random.randint(1, 3))
    return ' '.join([word.capitalize() for word in words])


class MemberFactory(factory.Factory):
    class Meta:
        model = Member

    programme = random.choice(['computingscience', 'informationscience'])
    student_number = factory.LazyAttribute(
        lambda x: faker.numerify(text="s#######"))
    starting_year = factory.LazyAttribute(
        lambda x: random.randint(1990, date.today().year))

    address_street = factory.LazyAttribute(lambda x: faker.street_address())
    address_postal_code = factory.LazyAttribute(lambda x: faker.postcode())
    address_city = factory.LazyAttribute(lambda x: faker.city())

    phone_number = '+31' + faker.numerify(text="##########")


class Command(BaseCommand):
    help = "Creates fake data to test the site with"

    def add_arguments(self, parser):
        parser.add_argument(
            "-b",
            "--board",
            type=int,
            help="The amount of fake boards to add")
        parser.add_argument(
            "-c",
            "--committee",
            type=int,
            help="The amount of fake committees to add")
        parser.add_argument(
            "-e",
            "--event",
            type=int,
            help="The amount of fake events to add")
        parser.add_argument(
            "-p",
            "--partner",
            type=int,
            help="The amount of fake partners to add")
        parser.add_argument(
            "-i",
            "--pizza",
            type=int,
            help="The amount of fake pizzas to add")
        parser.add_argument(
            "-u",
            "--user",
            type=int,
            help="The amount of fake users to add")
        parser.add_argument(
            "-w",
            "--vacancy",
            type=int,
            help="The amount of fake vacancies to add")

    def create_board(self, lecture_year, members):
        board = Board()

        board.name_nl = "Bestuur {}-{}".format(lecture_year, lecture_year+1)
        board.name_en = "Board {}-{}".format(lecture_year, lecture_year+1)
        board.description_nl = faker.paragraph()
        board.description_en = faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(board.name_nl, 480, 480, (
            10, 10, 10,
            10))  # 620x620 pixels, with 10 pixels padding on each side
        with tempfile.TemporaryFile() as tfile:
            tfile.write(icon)
            board.photo.save(board.name_nl + '.png', File(tfile))

        board.since = date(year=lecture_year, month=9, day=1)
        board.until = date(year=lecture_year+1, month=8, day=31)
        board.active = True
        board.contact_email = faker.email()

        board.save()

        # Add members
        board_members = random.sample(list(members), random.randint(5, 6))
        for member in board_members:
            self.create_committee_membership(member, board)

        # Make one member the chair
        chair = random.choice(board.committeemembership_set.all())
        chair.until = None
        chair.chair = True
        chair.save()

    def create_committee(self, members):
        committee = Committee()

        committee.name_nl = generate_title()
        committee.name_en = committee.name_nl
        committee.description_nl = faker.paragraph()
        committee.description_en = faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(committee.name_nl, 480, 480, (
            10, 10, 10,
            10))  # 620x620 pixels, with 10 pixels padding on each side
        with tempfile.TemporaryFile() as tfile:
            tfile.write(icon)
            committee.photo.save(committee.name_nl + '.png', File(tfile))

        committee.since = faker.date_time_between("-10y", "+30d")

        if random.random() < 0.1:
            now = date.today()
            month = timedelta(days=30)
            committee.until = faker.date_time_between_dates(committee.since,
                                                            now + 2 *
                                                            month).date()

        committee.active = random.random() < 0.9
        committee.contact_email = faker.email()

        committee.save()

        # Add members
        committee_members = random.sample(list(members), random.randint(5, 20))
        for member in committee_members:
            self.create_committee_membership(member, committee)

        # Make one member the chair
        chair = random.choice(committee.committeemembership_set.all())
        chair.until = None
        chair.chair = True
        chair.save()

    def create_committee_membership(self, member, committee):
        membership = CommitteeMembership()

        membership.member = member
        membership.committee = committee

        today = date.today()
        month = timedelta(days=30)
        membership.since = faker.date_time_between_dates(committee.since,
                                                         today + month).date()

        if random.random() < 0.2 and membership.since < today:
            membership.until = faker.date_time_between_dates(membership.since,
                                                             today).date()

        membership.save()

    def create_event(self, committees):
        event = Event()

        event.title_nl = generate_title()
        event.title_en = event.title_nl
        event.description_nl = faker.paragraph()
        event.description_en = faker.paragraph()
        event.start = faker.date_time_between("-1y", "+3m", current_tz)
        duration = math.ceil(random.expovariate(0.2))
        event.end = event.start + timedelta(hours=duration)
        event.organiser = random.choice(committees)
        event.category = random.choice(Event.EVENT_CATEGORIES)

        if random.random() < 0.5:
            week = timedelta(days=7)
            event.registration_start = faker.date_time_between_dates(
                    start_date=event.start - 4*week,
                    end_date=event.start - week,
                    tzinfo=current_tz)
            event.registration_end = faker.date_time_between_dates(
                    start_date=event.registration_start,
                    end_date=event.start,
                    tzinfo=current_tz)
            event.cancel_deadline = faker.date_time_between_dates(
                    start_date=event.registration_end,
                    end_date=event.start,
                    tzinfo=current_tz)

        event.location_nl = faker.street_address()
        event.location_en = event.location_nl
        event.map_location = event.location_nl

        if random.random() < 0.5:
            event.price = random.randint(100, 2500) / 100
            event.fine = max(
                    5.0,
                    random.randint(round(100 * event.price),
                                   round(500 * event.price)) / 100)

        if random.random() < 0.5:
            event.max_participants = random.randint(20, 200)

        event.published = random.random() < 0.9

        event.save()

    def create_partner(self):
        partner = Partner()

        partner.is_active = random.random() < 0.75
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

        partner.save()

    def create_pizza(self, prod_type):
        product = Product()

        product.name = prod_type + ' ' + pizza_name_faker.last_name()
        product.description_nl = faker.sentence()
        product.description_nl = faker.sentence()
        product.price = random.randint(250, 1000) / 100
        product.available = random.random() < 0.9

        product.save()

    def create_user(self):
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
            start_date='-2y', end_date='+2y', tzinfo=None), None])
        membership.type = random.choice(
            ['member', 'supporter', 'honorary'])

        user.save()
        member.save()
        membership.save()

    def create_vacancy(self, partners, categories):
        vacancy = Vacancy()

        vacancy.title = faker.job()
        vacancy.description = faker.paragraph()
        vacancy.link = faker.uri()
        vacancy.partner = random.choice(partners)

        if random.random() < 0.5:
            vacancy.expiration_date = faker.date_time_between("-1y", "+1y")

        vacancy.save()

        vacancy.categories = random.sample(list(categories),
                                           random.randint(0, 3))

    def create_vacancy_category(self):
        category = VacancyCategory()

        category.name_nl = faker.text(max_nb_chars=30)
        category.name_en = faker.text(max_nb_chars=30)
        category.slug = faker.slug()

        category.save()

    def handle(self, **options):
        opts = ['board', 'committee', 'event', 'partner', 'pizza', 'user',
                'vacancy']

        if all([not options[opt] for opt in opts]):
            print("Use ./manage.py help createfixtures to find out how to call"
                  " this command")

        # Users need to be generated before boards and committees
        if options['user']:
            for __ in range(options['user']):
                self.create_user()

        if options['board']:
            members = Member.objects.all()
            lecture_year = datetime_to_lectureyear(date.today())
            for i in range(options['board']):
                self.create_board(lecture_year - i, members)

        # Committees need to be generated before events
        if options['committee']:
            members = Member.objects.all()
            for __ in range(options['committee']):
                self.create_committee(members)

        if options['event']:
            committees = Committee.objects.all()
            for __ in range(options['event']):
                self.create_event(committees)

        # Partners need to be generated before vacancies
        if options['partner']:
            for __ in range(options['partner']):
                self.create_partner()

            # Make one of the partners the main partner
            try:
                Partner.objects.get(is_main_partner=True)
            except Partner.DoesNotExist:
                main_partner = random.choice(Partner.objects.all())
                main_partner.is_active = True
                main_partner.is_main_partner = True
                main_partner.save()

        if options['vacancy']:
            categories = VacancyCategory.objects.all()
            if not categories:
                for __ in range(5):
                    self.create_vacancy_category()
                categories = VacancyCategory.objects.all()

            partners = Partner.objects.all()
            for __ in range(options['vacancy']):
                self.create_vacancy(partners, categories)

        if options['pizza']:
            num_pizzas = random.randint(0, options['pizza'])
            for __ in range(num_pizzas):
                self.create_pizza('Pizza')

            num_pastas = options['pizza'] - num_pizzas
            for __ in range(num_pastas):
                self.create_pizza('Pasta')
