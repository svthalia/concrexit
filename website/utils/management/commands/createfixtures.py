"""
Provides the command to generate fixtures
"""
# pylint: disable=invalid-name,no-member,too-few-public-methods
# pylint: disable=attribute-defined-outside-init,no-self-use
import math
import random
import string
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from activemembers.models import (Board, Committee, MemberGroupMembership,
                                  Society, MemberGroup)
from documents.models import Document
from events.models import Event
from members.models import Profile, Member, Membership
from newsletters.models import NewsletterItem, NewsletterEvent, Newsletter
from partners.models import Partner, Vacancy, VacancyCategory
from pizzas.models import Product
from utils.snippets import datetime_to_lectureyear

try:
    import factory
    from faker import Factory as FakerFactory
    from pydenticon import Generator as IconGenerator
except ImportError as error:
    raise Exception("Have you installed the dev-requirements? "
                    "Failed importing {}".format(error)) from error

_faker = FakerFactory.create('nl_NL')
_pizza_name_faker = FakerFactory.create('it_IT')
_current_tz = timezone.get_current_timezone()


def _generate_title():
    words = _faker.words(random.randint(1, 3))
    return ' '.join([word.capitalize() for word in words])


class _ProfileFactory(factory.Factory):
    class Meta:  # pylint: disable=missing-docstring
        model = Profile

    programme = random.choice(['computingscience', 'informationscience'])
    student_number = factory.LazyAttribute(
        lambda x: _faker.numerify(text="s#######"))
    starting_year = factory.LazyAttribute(
        lambda x: random.randint(1990, date.today().year))

    address_street = factory.LazyAttribute(lambda x: _faker.street_address())
    address_postal_code = factory.LazyAttribute(lambda x: _faker.postcode())
    address_city = factory.LazyAttribute(lambda x: _faker.city())
    address_country = random.choice(['NL', 'DE', 'BE'])

    phone_number = '+31{}'.format(_faker.numerify(text="##########"))


class Command(BaseCommand):
    """Command to create fake data to populate the site"""
    help = "Creates fake data to test the site with"

    def add_arguments(self, parser):
        """
        Adds arguments to the argument parser.

        :param parser: the argument parser
        """
        parser.add_argument(
            "-a",
            "--all",
            action='store_true',
            help="Fully populate a database with fixtures")
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
            "-d",
            "--document",
            type=int,
            help="The amount of fake miscellaneous documents to add")
        parser.add_argument(
            "-e",
            "--event",
            type=int,
            help="The amount of fake events to add")
        parser.add_argument(
            "-n",
            "--newsletter",
            type=int,
            help="The amount of fake newsletters to add")
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
            "-s",
            "--society",
            type=int,
            help="The amount of fake societies to add")
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

    def create_board(self, lecture_year):
        """
        Create a new board

        :param int lecture_year: the  lecture year this board was active
        """
        members = Member.objects.all()
        if len(members) < 6:
            print('Your database does not contain 6 users.')
            print(f'Creating {6 - len(members)} more users.')
            for __ in range(6 - len(members)):
                self.create_user()

        board = Board()

        board.name_nl = "Bestuur {}-{}".format(lecture_year, lecture_year + 1)
        board.name_en = "Board {}-{}".format(lecture_year, lecture_year + 1)
        board.description_nl = _faker.paragraph()
        board.description_en = _faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            board.name_nl, 480, 480,
            padding=(10, 10, 10, 10),
            output_format='jpeg',
        )  # 620x620 pixels, with 10 pixels padding on each side
        board.photo.save(board.name_nl + '.jpeg', ContentFile(icon))

        board.since = date(year=lecture_year, month=9, day=1)
        board.until = date(year=lecture_year + 1, month=8, day=31)
        board.active = True
        board.contact_email = _faker.email()

        board.save()

        # Add members
        board_members = random.sample(list(members), random.randint(5, 6))
        for member in board_members:
            self.create_member_group_membership(member, board)

        # Make one member the chair
        chair = random.choice(board.membergroupmembership_set.all())
        chair.until = None
        chair.chair = True
        chair.save()

    def create_member_group(self, group_model):
        """
        Create a MemberGroup
        """
        members = Member.objects.all()
        if len(members) < 6:
            print('Your database does not contain 6 users.')
            print(f'Creating {6 - len(members)} more users.')
            for __ in range(6 - len(members)):
                self.create_user()
            members = Member.objects.all()

        member_group = group_model()

        member_group.name_nl = _generate_title()
        member_group.name_en = member_group.name_nl
        member_group.description_nl = _faker.paragraph()
        member_group.description_en = _faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            member_group.name_nl, 480, 480,
            padding=(10, 10, 10, 10),
            output_format='jpeg',
        )  # 620x620 pixels, with 10 pixels padding on each side
        member_group.photo.save(
            member_group.name_nl + '.jpeg', ContentFile(icon))

        member_group.since = _faker.date_time_between("-10y", "+30d")

        if random.random() < 0.1:
            now = date.today()
            month = timedelta(days=30)
            member_group.until = _faker.date_time_between_dates(
                member_group.since, now + 2 * month).date()

        member_group.active = random.random() < 0.9
        member_group.contact_email = _faker.email()

        member_group.save()

        # Add members
        committee_members = random.sample(list(members), random.randint(2, 6))
        for member in committee_members:
            self.create_member_group_membership(member, member_group)

        # Make one member the chair
        chair = random.choice(member_group.membergroupmembership_set.all())
        chair.until = None
        chair.chair = True
        chair.save()

    def create_member_group_membership(self, member, group):
        """
        Create member group membership

        :param member: the member to add to the committee
        :param group: the group to add the member to
        """
        membership = MemberGroupMembership()

        membership.member = member
        membership.group = group

        today = date.today()
        month = timedelta(days=30)
        membership.since = _faker.date_time_between_dates(group.since,
                                                          today + month).date()

        if random.random() < 0.2 and membership.since < today:
            membership.until = _faker.date_time_between_dates(membership.since,
                                                              today).date()

        membership.save()

    def create_event(self):
        """
        Create an event
        """
        groups = MemberGroup.objects.all()
        if len(groups) == 0:
            print('Your database does not contain any member groups.')
            print('Creating a committee.')
            self.create_member_group(Committee)
            groups = MemberGroup.objects.all()
        event = Event()

        event.title_nl = _generate_title()
        event.title_en = event.title_nl
        event.description_nl = _faker.paragraph()
        event.description_en = _faker.paragraph()
        event.start = _faker.date_time_between("-30d", "+120d", _current_tz)
        duration = math.ceil(random.expovariate(0.2))
        event.end = event.start + timedelta(hours=duration)
        event.organiser = random.choice(groups)
        event.category = random.choice(Event.EVENT_CATEGORIES)

        if random.random() < 0.5:
            week = timedelta(days=7)
            event.registration_start = _faker.date_time_between_dates(
                datetime_start=event.start - 4 * week,
                datetime_end=event.start - week,
                tzinfo=_current_tz)
            event.registration_end = _faker.date_time_between_dates(
                datetime_start=event.registration_start,
                datetime_end=event.start,
                tzinfo=_current_tz)
            event.cancel_deadline = _faker.date_time_between_dates(
                datetime_start=event.registration_end,
                datetime_end=event.start,
                tzinfo=_current_tz)

        event.location_nl = _faker.street_address()
        event.location_en = event.location_nl
        event.map_location = event.location_nl
        event.send_cancel_email = False

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
        """Create a new random partner"""
        partner = Partner()

        partner.is_active = random.random() < 0.75
        partner.name = '{} {}'.format(
            _faker.company(),
            _faker.company_suffix()
        )
        partner.slug = _faker.slug()
        partner.link = _faker.uri()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            partner.name, 480, 480,
            padding=(10, 10, 10, 10),
            output_format='jpeg',
        )  # 620x620 pixels, with 10 pixels padding on each side
        partner.logo.save(partner.name + '.jpeg', ContentFile(icon))

        partner.address = _faker.street_address()
        partner.zip_code = _faker.postcode()
        partner.city = _faker.city()

        partner.save()

    def create_pizza(self):
        """Create a new random pizza product"""
        product = Product()

        product.name = f'Pizza {_pizza_name_faker.last_name()}'
        product.description_nl = _faker.sentence()
        product.description_nl = _faker.sentence()
        product.price = random.randint(250, 1000) / 100
        product.available = random.random() < 0.9

        product.save()

    def create_user(self):
        """Create a new random user"""
        fakeprofile = _faker.profile()
        fakeprofile['password'] = ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(16))
        user = User.objects.create_user(fakeprofile['username'],
                                        fakeprofile['mail'],
                                        fakeprofile['password'])
        user.first_name = fakeprofile['name'].split()[0]
        user.last_name = ' '.join(fakeprofile['name'].split()[1:])

        profile = _ProfileFactory()
        profile.user_id = user.id
        profile.birthday = fakeprofile['birthdate']
        profile.website = fakeprofile['website'][0]

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            user.username, 480, 480,
            padding=(10, 10, 10, 10),
            output_format='jpeg',
        )  # 620x620 pixels, with 10 pixels padding on each side
        profile.photo.save(fakeprofile['username'] + '.jpeg',
                           ContentFile(icon))

        membership = Membership()
        membership.user_id = user.id
        membership.since = _faker.date_time_between(
            start_date='-4y', end_date='now', tzinfo=None)
        membership.until = random.choice([_faker.date_time_between(
            start_date='-2y', end_date='+2y', tzinfo=None), None])
        membership.type = random.choice(
            [t[0] for t in Membership.MEMBERSHIP_TYPES])

        user.save()
        profile.save()
        membership.save()

    def create_vacancy(self, partners, categories):
        """
        Create a new random vacancy

        :param partners: the partners to choose a partner from
        :param categories: the categories to choose this vacancy from
        """
        vacancy = Vacancy()

        vacancy.title = _faker.job()
        vacancy.description = _faker.paragraph(nb_sentences=10)
        vacancy.link = _faker.uri()

        if random.random() < 0.75:
            vacancy.partner = random.choice(partners)
        else:
            vacancy.company_name = '{} {}'.format(
                _faker.company(),
                _faker.company_suffix()
            )
            igen = IconGenerator(5, 5)  # 5x5 blocks
            icon = igen.generate(
                vacancy.company_name, 480, 480,
                padding=(10, 10, 10, 10),
                output_format='jpeg',
            )  # 620x620 pixels, with 10 pixels padding on each side
            vacancy.company_logo.save(vacancy.company_name + '.jpeg',
                                      ContentFile(icon))

        if random.random() < 0.5:
            vacancy.expiration_date = _faker.date_time_between("-1y", "+1y")

        vacancy.save()

        vacancy.categories.set(random.sample(list(categories),
                                             random.randint(0, 3)))

    def create_vacancy_category(self):
        """Create new random vacancy categories"""
        category = VacancyCategory()

        category.name_nl = _faker.text(max_nb_chars=30)
        category.name_en = _faker.text(max_nb_chars=30)
        category.slug = _faker.slug()

        category.save()

    def create_document(self):
        """Creates new random documents"""
        doc = Document()

        doc.name_nl = _faker.text(max_nb_chars=30)
        doc.name_en = _faker.text(max_nb_chars=30)
        doc.category = random.choice([c[0] for c in
                                      Document.DOCUMENT_CATEGORIES])
        doc.members_only = random.random() < 0.75
        doc.file_en.save('{}.txt'.format(doc.name_en), ContentFile(
            _faker.text(max_nb_chars=120)))
        doc.file_nl = doc.file_en
        doc.save()

    def create_newsletter(self):
        newsletter = Newsletter()

        newsletter.title_en = _generate_title()
        newsletter.title_nl = newsletter.title_en
        newsletter.description_nl = _faker.paragraph()
        newsletter.description_en = _faker.paragraph()
        newsletter.date = _faker.date_time_between("-3m", "+3m", _current_tz)

        newsletter.save()

        for i in range(random.randint(1, 5)):
            item = NewsletterItem()
            item.title_en = _generate_title()
            item.title_nl = item.title_en
            item.description_nl = _faker.paragraph()
            item.description_en = _faker.paragraph()
            item.newsletter = newsletter
            item.save()

        for i in range(random.randint(1, 5)):
            item = NewsletterEvent()
            item.title_en = _generate_title()
            item.title_nl = item.title_en
            item.description_nl = _faker.paragraph()
            item.description_en = _faker.paragraph()
            item.newsletter = newsletter

            item.what_en = item.title_en
            item.what_nl = item.what_en
            item.where_en = _faker.city()
            item.where_nl = item.where_en
            item.start_datetime = _faker.date_time_between("-1y", "+3m",
                                                           _current_tz)
            duration = math.ceil(random.expovariate(0.2))
            item.end_datetime = item.start_datetime + timedelta(hours=duration)

            if random.random() < 0.5:
                item.show_costs_warning = True
                item.price = random.randint(100, 2500) / 100
                item.penalty_costs = max(
                    5.0, random.randint(round(100 * item.price),
                                        round(500 * item.price)) / 100)

            item.save()

    def handle(self, *args, **options):  # pylint: disable=too-many-branches
        """
        Handle the command being executed

        :param options: the passed-in options
        """
        opts = ['all', 'board', 'committee', 'event', 'partner', 'pizza',
                'user', 'vacancy', 'document', 'newsletter']

        if all([not options[opt] for opt in opts]):
            print("Use ./manage.py help createfixtures to find out how to call"
                  " this command")

        if options['all']:
            print('all argument given, overwriting all other inputs')
            options = {
                'user': 20,
                'board': 3,
                'committee': 3,
                'society': 3,
                'event': 20,
                'partner': 6,
                'vacancy': 4,
                'pizza': 5,
                'newsletter': 2,
                'document': 8
            }

        # Users need to be generated before boards and committees
        if options['user']:
            for __ in range(options['user']):
                self.create_user()

        if options['board']:
            lecture_year = datetime_to_lectureyear(date.today())
            for i in range(options['board']):
                self.create_board(lecture_year - i)

        # Member groups need to be generated before events
        if options['committee']:
            for __ in range(options['committee']):
                self.create_member_group(Committee)

        if options['society']:
            for __ in range(options['society']):
                self.create_member_group(Society)

        if options['event']:
            for __ in range(options['event']):
                self.create_event()

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
                print('No vacancy categories found. Creating 5 categories.')
                for __ in range(5):
                    self.create_vacancy_category()
                categories = VacancyCategory.objects.all()

            partners = Partner.objects.all()
            for __ in range(options['vacancy']):
                self.create_vacancy(partners, categories)

        if options['pizza']:
            for __ in range(options['pizza']):
                self.create_pizza()

        if options['newsletter']:
            for __ in range(options['newsletter']):
                self.create_newsletter()

        if options['document']:
            for __ in range(options['document']):
                self.create_document()
