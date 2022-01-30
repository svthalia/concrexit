import logging
import os

from PIL import Image
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from utils import countries

logger = logging.getLogger(__name__)


def _profile_image_path(_instance, _filename):
    """Set the upload path for profile images.

    Makes sure that it's hard to enumerate profile images.

    Also makes sure any user-picked filenames don't survive

    >>> _profile_image_path(None, "bla.jpg")
    public/avatars/...
    >>> "swearword" in _profile_image_path(None, "swearword.jpg")
    False
    """
    return f"public/avatars/{get_random_string(length=16)}"


class Profile(models.Model):
    """This class holds extra information about a member."""

    # No longer yearly membership as a type, use expiration date instead.
    PROGRAMME_CHOICES = (
        ("computingscience", _("Computing Science")),
        ("informationscience", _("Information Sciences")),
    )

    # Preferably this would have been a foreign key to Member instead,
    # but the UserAdmin requires that this is a foreign key to User.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # ----- Registration information -----

    programme = models.CharField(
        max_length=20,
        choices=PROGRAMME_CHOICES,
        verbose_name=_("Study programme"),
        blank=True,
        null=True,
    )

    student_number = models.CharField(
        verbose_name=_("Student number"),
        max_length=8,
        validators=[
            validators.RegexValidator(
                regex=r"(s\d{7}|[ezu]\d{6,7})",
                message=_("Enter a valid student- or e/z/u-number."),
            )
        ],
        blank=True,
        null=True,
        unique=True,
    )

    starting_year = models.IntegerField(
        verbose_name=_("Starting year"),
        help_text=_("The year this member started studying."),
        blank=True,
        null=True,
    )

    # ---- Address information -----

    address_street = models.CharField(
        max_length=100,
        validators=[
            validators.RegexValidator(
                regex=r"^.+ \d+.*",
                message=_("please use the format <street> <number>"),
            )
        ],
        verbose_name=_("Street and house number"),
        null=True,
    )

    address_street2 = models.CharField(
        max_length=100,
        verbose_name=_("Second address line"),
        blank=True,
        null=True,
    )

    address_postal_code = models.CharField(
        max_length=10,
        verbose_name=_("Postal code"),
        null=True,
    )

    address_city = models.CharField(
        max_length=40,
        verbose_name=_("City"),
        null=True,
    )

    address_country = models.CharField(
        max_length=2,
        choices=countries.EUROPE,
        verbose_name=_("Country"),
        null=True,
    )

    phone_number = models.CharField(
        max_length=20,
        verbose_name=_("Phone number"),
        help_text=_("Enter a phone number so Thalia may reach you"),
        validators=[
            validators.RegexValidator(
                regex=r"^\+?\d+$",
                message=_("Please enter a valid phone number"),
            )
        ],
        null=True,
        blank=True,
    )

    # ---- Emergency contact ----

    emergency_contact = models.CharField(
        max_length=255,
        verbose_name=_("Emergency contact name"),
        help_text=_("Who should we contact in case of emergencies"),
        null=True,
        blank=True,
    )

    emergency_contact_phone_number = models.CharField(
        max_length=20,
        verbose_name=_("Emergency contact phone number"),
        help_text=_("The phone number for the emergency contact"),
        validators=[
            validators.RegexValidator(
                regex=r"^\+?\d+$",
                message=_("Please enter a valid phone number"),
            )
        ],
        null=True,
        blank=True,
    )

    # ---- Personal information ------

    birthday = models.DateField(verbose_name=_("Birthday"), null=True)

    show_birthday = models.BooleanField(
        verbose_name=_("Display birthday"),
        help_text=_(
            "Show your birthday to other members on your profile page and "
            "in the birthday calendar"
        ),
        default=True,
    )

    website = models.URLField(
        max_length=200,
        verbose_name=_("Website"),
        help_text=_("Website to display on your profile page"),
        blank=True,
        null=True,
    )

    profile_description = models.TextField(
        verbose_name=_("Profile text"),
        help_text=_("Text to display on your profile"),
        blank=True,
        null=True,
        max_length=4096,
    )

    initials = models.CharField(
        max_length=20,
        verbose_name=_("Initials"),
        blank=True,
        null=True,
    )

    nickname = models.CharField(
        max_length=30,
        verbose_name=_("Nickname"),
        blank=True,
        null=True,
    )

    display_name_preference = models.CharField(
        max_length=10,
        verbose_name=_("How to display name"),
        choices=(
            ("full", _("Show full name")),
            ("nickname", _("Show only nickname")),
            ("firstname", _("Show only first name")),
            ("initials", _("Show initials and last name")),
            ("fullnick", _("Show name like \"John 'nickname' Doe\"")),
            ("nicklast", _("Show nickname and last name")),
        ),
        default="full",
    )

    photo = models.ImageField(
        verbose_name=_("Photo"),
        upload_to=_profile_image_path,
        null=True,
        blank=True,
    )

    event_permissions = models.CharField(
        max_length=9,
        verbose_name=_("Which events can this member attend"),
        choices=(
            ("all", _("All events")),
            ("no_events", _("User may not attend events")),
            ("no_drinks", _("User may not attend drinks")),
            ("nothing", _("User may not attend anything")),
        ),
        default="all",
    )

    # --- Communication preference ----

    receive_optin = models.BooleanField(
        verbose_name=_("Receive opt-in mailings"),
        help_text=_(
            "Receive mailings about vacancies and events from Thalia's partners."
        ),
        default=True,
    )

    receive_newsletter = models.BooleanField(
        verbose_name=_("Receive newsletter"),
        help_text=_("Receive the Thalia Newsletter"),
        default=True,
    )

    receive_magazine = models.BooleanField(
        verbose_name=_("Receive the Thabloid"),
        help_text=_("Receive printed Thabloid magazines"),
        default=True,
    )

    # --- Active Member preference ---
    email_gsuite_only = models.BooleanField(
        verbose_name=_("Only receive Thalia emails on G Suite-account"),
        help_text=_(
            "If you enable this option you will no longer receive "
            "emails send to you by Thalia on your personal email "
            "address. We will only use your G Suite email address."
        ),
        default=False,
    )

    def display_name(self):
        # pylint: disable=too-many-return-statements
        pref = self.display_name_preference
        if pref == "nickname" and self.nickname is not None:
            return f"'{self.nickname}'"
        if pref == "firstname":
            return self.user.first_name
        if pref == "initials":
            if self.initials:
                return "{} {}".format(self.initials, self.user.last_name)
            return self.user.last_name
        if pref == "fullnick" and self.nickname is not None:
            return "{} '{}' {}".format(
                self.user.first_name, self.nickname, self.user.last_name
            )
        if pref == "nicklast" and self.nickname is not None:
            return "'{}' {}".format(self.nickname, self.user.last_name)
        return self.user.get_full_name() or self.user.username

    display_name.short_description = _("Display name")

    def short_display_name(self):
        pref = self.display_name_preference
        if self.nickname is not None and pref in ("nickname", "nicklast"):
            return f"'{self.nickname}'"
        if pref == "initials":
            if self.initials:
                return "{} {}".format(self.initials, self.user.last_name)
            return self.user.last_name
        return self.user.first_name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.photo:
            self._orig_image = self.photo.name
        else:
            self._orig_image = ""

    def clean(self):
        super().clean()
        errors = {}

        if self.display_name_preference in ("nickname", "fullnick", "nicklast"):
            if not self.nickname:
                errors.update(
                    {
                        "nickname": _(
                            "You need to enter a nickname to use it as display name"
                        )
                    }
                )

        if self.birthday and self.birthday > timezone.now().date():
            errors.update({"birthday": _("A birthday cannot be in the future.")})

        if errors:
            raise ValidationError(errors)

    def save(self, **kwargs):
        super().save(**kwargs)
        storage = DefaultStorage()

        if self._orig_image and not self.photo:
            storage.delete(self._orig_image)
            self._orig_image = None

        elif self.photo and self._orig_image != self.photo.name:
            original_image_name = self.photo.name
            logger.debug("Converting image %s", original_image_name)

            with self.photo.open() as image_handle:
                image = Image.open(image_handle)
                image.load()

            # Image.thumbnail does not upscale an image that is smaller
            image.thumbnail(settings.PHOTO_UPLOAD_SIZE, Image.ANTIALIAS)

            # Create new filename to store compressed image
            image_name, _ext = os.path.splitext(original_image_name)
            image_name = storage.get_available_name(f"{image_name}.jpg")
            with storage.open(image_name, "wb") as new_image_file:
                image.convert("RGB").save(new_image_file, "JPEG")
            self.photo.name = image_name
            super().save(**kwargs)

            # delete original upload.
            storage.delete(original_image_name)

            if self._orig_image:
                logger.info("deleting: %s", self._orig_image)
                storage.delete(self._orig_image)
            self._orig_image = self.photo.name
        else:
            logging.info("We already had this image, skipping thumbnailing")

    def __str__(self):
        return _("Profile for {}").format(self.user)
