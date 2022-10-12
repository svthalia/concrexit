"""Provides the command to generate fixtures."""

# pylint: disable=too-many-statements,too-many-branches
import math
import random
import string
from datetime import date, timedelta, datetime

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from activemembers.models import (
    Board,
    Committee,
    MemberGroupMembership,
    Society,
    MemberGroup,
)
from documents.models import Document
from education.models import Course, Category
from events.models import (
    Event,
    EventRegistration,
    EVENT_CATEGORIES,
    registration_member_choices_limit,
)
from members.models import Profile, Member, Membership
from newsletters.models import NewsletterItem, NewsletterEvent, Newsletter
from partners.models import Partner, Vacancy, VacancyCategory
from payments.models import Payment
from payments.services import create_payment
from photos.models import Album, Photo
from pizzas.models import Product
from utils.snippets import datetime_to_lectureyear

try:
    import factory
    from faker import Factory as FakerFactory
    from pydenticon import Generator as IconGenerator
except ImportError as error:
    raise Exception(
        "Have you installed the dev-requirements? Failed importing {}".format(error)
    ) from error

_faker = FakerFactory.create("nl_NL")
_pizza_name_faker = FakerFactory.create("it_IT")
_current_tz = timezone.get_current_timezone()


def _generate_title():
    words = _faker.words(random.randint(1, 3))
    return " ".join([word.capitalize() for word in words])


class _ProfileFactory(factory.Factory):
    class Meta:
        model = Profile

    programme = random.choice(["computingscience", "informationscience"])
    student_number = factory.LazyAttribute(lambda x: _faker.numerify(text="s#######"))
    starting_year = factory.LazyAttribute(
        lambda x: random.randint(1990, date.today().year)
    )

    address_street = factory.LazyAttribute(lambda x: _faker.street_address())
    address_postal_code = factory.LazyAttribute(lambda x: _faker.postcode())
    address_city = factory.LazyAttribute(lambda x: _faker.city())
    address_country = random.choice(["NL", "DE", "BE"])

    phone_number = "+31{}".format(_faker.numerify(text="##########"))


def get_event_to_register_for(member):
    for event in Event.objects.filter(published=True).order_by("?"):
        if event.registration_required and not event.reached_participants_limit():
            if member.id not in event.registrations.values_list("member", flat=True):
                return event
    return None


class Command(BaseCommand):
    """Command to create fake data to populate the site."""

    help = "Creates fake data to test the site with"

    def add_arguments(self, parser):
        """Add arguments to the argument parser.

        :param parser: the argument parser
        """
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Fully populate a database with fixtures",
        )
        parser.add_argument(
            "-b", "--board", type=int, help="The amount of fake boards to add"
        )
        parser.add_argument(
            "-c", "--committee", type=int, help="The amount of fake committees to add"
        )
        parser.add_argument(
            "-d",
            "--document",
            type=int,
            help="The amount of fake miscellaneous documents to add",
        )
        parser.add_argument(
            "-e", "--event", type=int, help="The amount of fake events to add"
        )
        parser.add_argument(
            "-n", "--newsletter", type=int, help="The amount of fake newsletters to add"
        )
        parser.add_argument(
            "-p", "--partner", type=int, help="The amount of fake partners to add"
        )
        parser.add_argument(
            "-i", "--pizza", type=int, help="The amount of fake pizzas to add"
        )
        parser.add_argument(
            "-s", "--society", type=int, help="The amount of fake societies to add"
        )
        parser.add_argument(
            "-u", "--user", type=int, help="The amount of fake users to add"
        )
        parser.add_argument(
            "-w", "--vacancy", type=int, help="The amount of fake vacancies to add"
        )
        parser.add_argument("--course", type=int, help="The amount of courses to add")
        parser.add_argument(
            "-r",
            "--registration",
            type=int,
            help="The amount of event registrations to add",
        )
        parser.add_argument("--payment", type=int, help="The amount of payments to add")
        parser.add_argument(
            "--photoalbum", type=int, help="The amount of photo albums to add"
        )

    def create_board(self, lecture_year):
        """Create a new board.

        :param int lecture_year: the  lecture year this board was active
        """
        self.stdout.write("Creating a board")
        members = Member.objects.all()
        if len(members) < 6:
            self.stdout.write("Your database does not contain 6 users.")
            self.stdout.write(f"Creating {6 - len(members)} more users.")
            for __ in range(6 - len(members)):
                self.create_user()

        board = Board()

        board.name = "Board {}-{}".format(lecture_year, lecture_year + 1)
        while Board.objects.filter(name=board.name).exists():
            lecture_year = lecture_year - 1
            board.name = "Board {}-{}".format(lecture_year, lecture_year + 1)

        board.description = _faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            board.name, 480, 480, padding=(10, 10, 10, 10), output_format="jpeg"
        )  # 620x620 pixels, with 10 pixels padding on each side
        board.photo.save(f"{board.name}.jpeg", ContentFile(icon))

        board.since = date(year=lecture_year, month=9, day=1)
        board.until = date(year=lecture_year + 1, month=8, day=31)
        board.active = True
        board.contact_email = _faker.safe_email()

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
        """Create a MemberGroup."""
        self.stdout.write("Creating a membergroup")
        members = Member.objects.all()
        if len(members) < 6:
            self.stdout.write("Your database does not contain 6 users.")
            self.stdout.write(f"Creating {6 - len(members)} more users.")
            for __ in range(6 - len(members)):
                self.create_user()
            members = Member.objects.all()

        member_group = group_model()

        member_group.name = _generate_title()
        member_group.description = _faker.paragraph()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            member_group.name,
            480,
            480,
            padding=(10, 10, 10, 10),
            output_format="jpeg",
        )  # 620x620 pixels, with 10 pixels padding on each side
        member_group.photo.save(member_group.name + ".jpeg", ContentFile(icon))

        member_group.since = _faker.date_time_between("-10y", "+30d")

        if random.random() < 0.1:
            now = date.today()
            month = timedelta(days=30)
            member_group.until = _faker.date_time_between_dates(
                member_group.since, now + 2 * month
            ).date()

        member_group.active = random.random() < 0.9
        member_group.contact_email = _faker.safe_email()

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
        """Create member group membership.

        :param member: the member to add to the committee
        :param group: the group to add the member to
        """
        self.stdout.write("Creating a group membership")
        membership = MemberGroupMembership()

        membership.member = member
        membership.group = group

        today = date.today()
        month = timedelta(days=30)
        membership.since = _faker.date_time_between_dates(
            group.since, today + month
        ).date()

        if random.random() < 0.2 and membership.since < today:
            membership.until = _faker.date_time_between_dates(
                membership.since, today
            ).date()

        membership.save()

    def create_event(self):
        """Create an event."""
        groups = MemberGroup.objects.all()
        if len(groups) == 0:
            self.stdout.write("Your database does not contain any member groups.")
            self.stdout.write("Creating a committee.")
            self.create_member_group(Committee)
            groups = MemberGroup.objects.all()
        event = Event()

        event.description = _faker.paragraph()
        event.title = _generate_title()
        event.start = _faker.date_time_between("-30d", "+120d", _current_tz)
        duration = math.ceil(random.expovariate(0.2))
        event.end = event.start + timedelta(hours=duration)
        event.save()
        event.organisers.add(*random.sample(list(groups), random.randint(1, 3)))
        event.category = random.choice(EVENT_CATEGORIES)[0]
        event.fine = 5

        if random.random() < 0.5:
            week = timedelta(days=7)
            event.registration_start = _faker.date_time_between_dates(
                datetime_start=event.start - 4 * week,
                datetime_end=event.start - week,
                tzinfo=_current_tz,
            )
            event.registration_end = _faker.date_time_between_dates(
                datetime_start=event.registration_start,
                datetime_end=event.start,
                tzinfo=_current_tz,
            )
            event.cancel_deadline = _faker.date_time_between_dates(
                datetime_start=event.registration_end,
                datetime_end=event.start,
                tzinfo=_current_tz,
            )

        event.location_en = _faker.street_address()
        event.map_location = event.location_en
        event.send_cancel_email = False

        if random.random() < 0.5:
            event.price = random.randint(100, 2500) / 100
            event.fine = max(
                5.0,
                random.randint(round(100 * event.price), round(500 * event.price))
                / 100,
            )

        if random.random() < 0.5:
            event.max_participants = random.randint(20, 200)

        event.published = random.random() < 0.9

        event.save()

    def create_partner(self):
        """Create a new random partner."""
        self.stdout.write("Creating a partner")
        partner = Partner()

        partner.is_active = random.random() < 0.75
        partner.name = "{} {}".format(_faker.company(), _faker.company_suffix())
        partner.slug = _faker.slug()
        partner.link = _faker.uri()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            partner.name,
            480,
            480,
            padding=(10, 10, 10, 10),
            output_format="jpeg",
        )  # 620x620 pixels, with 10 pixels padding on each side
        partner.logo.save(partner.name + ".jpeg", ContentFile(icon))

        partner.address = _faker.street_address()
        partner.zip_code = _faker.postcode()
        partner.city = _faker.city()

        partner.save()

    def create_pizza(self):
        """Create a new random pizza product."""
        self.stdout.write("Creating a pizza product")

        product = Product()

        product.name = f"Pizza {_pizza_name_faker.last_name()}"
        product.price = random.randint(250, 1000) / 100
        product.available = random.random() < 0.9

        product.save()

    def create_user(self):
        """Create a new random user."""
        self.stdout.write("Creating a user")

        fakeprofile = _faker.profile()
        fakeprofile["password"] = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(16)
        )
        user = get_user_model().objects.create_user(
            fakeprofile["username"], fakeprofile["mail"], fakeprofile["password"]
        )
        user.first_name = fakeprofile["name"].split()[0]
        user.last_name = " ".join(fakeprofile["name"].split()[1:])

        profile = _ProfileFactory()
        profile.user_id = user.id
        profile.birthday = fakeprofile["birthdate"]
        profile.website = fakeprofile["website"][0]

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            user.username,
            480,
            480,
            padding=(10, 10, 10, 10),
            output_format="jpeg",
        )  # 620x620 pixels, with 10 pixels padding on each side
        profile.photo.save(fakeprofile["username"] + ".jpeg", ContentFile(icon))

        membership = Membership()
        membership.user_id = user.id
        membership.since = _faker.date_time_between(
            start_date="-4y", end_date="now", tzinfo=None
        )
        membership.until = random.choice(
            [
                _faker.date_time_between(
                    start_date=membership.since, end_date="+2y", tzinfo=None
                ),
                None,
            ]
        )
        membership.type = random.choice([t[0] for t in Membership.MEMBERSHIP_TYPES])

        user.save()
        profile.save()
        membership.save()

    def create_vacancy(self, partners, categories):
        """Create a new random vacancy.

        :param partners: the partners to choose a partner from
        :param categories: the categories to choose this vacancy from
        """
        self.stdout.write("Creating a vacancy")
        vacancy = Vacancy()

        vacancy.title = _faker.job()
        vacancy.description = _faker.paragraph(nb_sentences=10)
        vacancy.link = _faker.uri()

        if random.random() < 0.75:
            vacancy.partner = random.choice(partners)
        else:
            vacancy.company_name = "{} {}".format(
                _faker.company(), _faker.company_suffix()
            )
            igen = IconGenerator(5, 5)  # 5x5 blocks
            icon = igen.generate(
                vacancy.company_name,
                480,
                480,
                padding=(10, 10, 10, 10),
                output_format="jpeg",
            )  # 620x620 pixels, with 10 pixels padding on each side
            vacancy.company_logo.save(vacancy.company_name + ".jpeg", ContentFile(icon))

        vacancy.save()

        vacancy.categories.set(random.sample(list(categories), random.randint(0, 3)))

    def create_vacancy_category(self):
        """Create new random vacancy categories."""
        self.stdout.write("Creating a new vacancy category")
        category = VacancyCategory()

        category.name_en = _faker.text(max_nb_chars=30)
        category.slug = _faker.slug()

        category.save()

    def create_document(self):
        """Create new random documents."""
        self.stdout.write("Creating a document")
        doc = Document()

        doc.name = _faker.text(max_nb_chars=30)
        doc.category = random.choice([c[0] for c in Document.DOCUMENT_CATEGORIES])
        doc.members_only = random.random() < 0.75
        doc.file.save(
            "{}.txt".format(doc.name), ContentFile(_faker.text(max_nb_chars=120))
        )
        doc.save()

    def create_newsletter(self):
        self.stdout.write("Creating a new newsletter")
        newsletter = Newsletter()

        newsletter.title = _generate_title()
        newsletter.description = _faker.paragraph()
        newsletter.date = _faker.date_time_between("-3m", "+3m", _current_tz)

        newsletter.save()

        for _ in range(random.randint(1, 5)):
            item = NewsletterItem()
            item.title = _generate_title()
            item.description = _faker.paragraph()
            item.newsletter = newsletter
            item.save()

        for _ in range(random.randint(1, 5)):
            item = NewsletterEvent()
            item.title = _generate_title()
            item.description = _faker.paragraph()
            item.newsletter = newsletter

            item.what = item.title
            item.where = _faker.city()
            item.start_datetime = _faker.date_time_between("-1y", "+3m", _current_tz)
            duration = math.ceil(random.expovariate(0.2))
            item.end_datetime = item.start_datetime + timedelta(hours=duration)

            if random.random() < 0.5:
                item.show_costs_warning = True
                item.price = random.randint(100, 2500) / 100
                item.penalty_costs = max(
                    5.0,
                    random.randint(round(100 * item.price), round(500 * item.price))
                    / 100,
                )

            item.save()

    def create_course(self):
        self.stdout.write("Creating a new course")
        course = Course()

        course.name = _generate_title()
        course.ec = 3 if random.random() < 0.5 else 6

        course.course_code = "NWI-" + "".join(random.choices(string.digits, k=5))

        course.since = random.randint(2016, 2020)
        if random.random() < 0.5:
            course.until = max(course.since + random.randint(1, 5), datetime.now().year)

        # Save so we can add categories
        course.save()

        for category in Category.objects.order_by("?")[: random.randint(1, 3)]:
            course.categories.add(category)

        course.save()

    def create_event_registration(self, event_to_register_for=None):
        self.stdout.write("Creating an event registration")
        registration = EventRegistration()

        eligible = Member.objects.filter(registration_member_choices_limit())
        registration.member = eligible.order_by("?")[0]

        possible_event = (
            event_to_register_for
            if event_to_register_for
            else get_event_to_register_for(registration.member)
        )

        if not possible_event:
            self.stdout.write("No possible events to register for")
            self.stdout.write("Creating a new event")
            self.create_event()
            possible_event = get_event_to_register_for(registration.member)

        if not possible_event:
            self.stdout.write("Could not create event")
            return

        registration.event = possible_event

        registration.date = registration.event.registration_start

        registration.save()

        return registration

    def create_payment(self):
        self.stdout.write("Creating a payment")

        possible_events = list(
            filter(
                lambda e: e.registrations.count() > 0,
                Event.objects.filter(price__gt=0).order_by("?"),
            )
        )
        if len(possible_events) == 0:
            print("No event where can be payed could be found, creating a new event")
            self.create_event()
            possible_events = list(
                filter(
                    lambda e: e.registrations.count() > 0,
                    Event.objects.filter(price__gt=0).order_by("?"),
                )
            )

        if len(possible_events) == 0:
            print("Could not create the event for an unexpected reason.")
            return

        event = possible_events[0]
        if len(event.registrations) == 0:
            print("No registrations found. Create some more registrations first")
            return

        registration = event.registrations.order_by("?")[0]

        superusers = Member.objects.filter(is_superuser=True)
        if not superusers:
            print(
                "There is no member which is also a superuser. Creating payments without this isn't possible!"
            )
            print("Please add an membership to the superuser.")
            return

        create_payment(
            registration,
            superusers[0],
            random.choice([Payment.CASH, Payment.CARD, Payment.WIRE]),
        )

    def create_photo_album(self):
        self.stdout.write("Creating a photo album")
        album = Album()

        album.title = _generate_title()

        album.date = _faker.date_between("-1y", "today")

        album.slug = slugify("-".join([str(album.date), album.title]))

        if random.random() < 0.25:
            album.hidden = True
        if random.random() < 0.5:
            album.shareable = True

        album.save()

        for _ in range(random.randint(20, 30)):
            self.create_photo(album)

    def create_photo(self, album):
        self.stdout.write("Creating a photo")
        photo = Photo()

        photo.album = album

        name = _generate_title()

        igen = IconGenerator(5, 5)  # 5x5 blocks
        icon = igen.generate(
            name,
            480,
            480,
            padding=(10, 10, 10, 10),
            output_format="jpeg",
        )  # 620x620 pixels, with 10 pixels padding on each side
        photo.file.save(f"{name}.jpeg", ContentFile(icon))

        photo.save()

    def handle(self, *args, **options):
        """Handle the command being executed.

        :param options: the passed-in options
        """
        opts = [
            "all",
            "board",
            "committee",
            "event",
            "partner",
            "pizza",
            "user",
            "vacancy",
            "document",
            "newsletter",
            "course",
            "registration",
            "payment",
            "photoalbum",
        ]

        if all([not options[opt] for opt in opts]):
            self.stdout.write(
                "Use ./manage.py help createfixtures to find out"
                " how to call this command"
            )

        if options["all"]:
            self.stdout.write("all argument given, overwriting all other inputs")
            options = {
                "user": 20,
                "board": 3,
                "committee": 3,
                "society": 3,
                "event": 20,
                "partner": 6,
                "vacancy": 4,
                "pizza": 5,
                "newsletter": 2,
                "document": 8,
                "course": 10,
                "registration": 20,
                "payment": 5,
                "photoalbum": 5,
            }

        # Users need to be generated before boards and committees
        if options["user"]:
            for __ in range(options["user"]):
                self.create_user()

        if options["board"]:
            lecture_year = datetime_to_lectureyear(date.today())
            for i in range(options["board"]):
                self.create_board(lecture_year - i)

        # Member groups need to be generated before events
        if options["committee"]:
            for __ in range(options["committee"]):
                self.create_member_group(Committee)

        if options["society"]:
            for __ in range(options["society"]):
                self.create_member_group(Society)

        if options["event"]:
            for __ in range(options["event"]):
                self.create_event()

        # Partners need to be generated before vacancies
        if options["partner"]:
            for __ in range(options["partner"]):
                self.create_partner()

            # Make one of the partners the main partner
            try:
                Partner.objects.get(is_main_partner=True)
            except Partner.DoesNotExist:
                main_partner = random.choice(Partner.objects.all())
                main_partner.is_active = True
                main_partner.is_main_partner = True
                main_partner.save()

        if options["vacancy"]:
            categories = VacancyCategory.objects.all()
            if not categories:
                self.stdout.write("No vacancy categories found. Creating 5 categories.")
                for __ in range(5):
                    self.create_vacancy_category()
                categories = VacancyCategory.objects.all()

            partners = Partner.objects.all()
            for __ in range(options["vacancy"]):
                self.create_vacancy(partners, categories)

        if options["pizza"]:
            for __ in range(options["pizza"]):
                self.create_pizza()

        if options["newsletter"]:
            for __ in range(options["newsletter"]):
                self.create_newsletter()

        if options["document"]:
            for __ in range(options["document"]):
                self.create_document()

        # Courses need to be created before exams and summaries
        if options["course"]:
            # Create course categories if needed
            if len(Category.objects.all()) < 5:
                for _ in range(5):
                    category = Category()
                    category.name = _generate_title()

                    category.save()

            for _ in range(options["course"]):
                self.create_course()

        # Registrations need to be created before payments
        if options["registration"]:
            for _ in range(options["registration"]):
                self.create_event_registration()

        if options["payment"]:
            for _ in range(options["payment"]):
                self.create_payment()

        if options["photoalbum"]:
            for _ in range(options["photoalbum"]):
                self.create_photo_album()
