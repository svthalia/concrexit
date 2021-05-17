"""The models defined by the registrations package."""
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.template.defaultfilters import floatformat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField, BICField

from members.models import Membership, Profile
from utils import countries


class Entry(models.Model):
    """Describes a registration entry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_("created at"), default=timezone.now)
    updated_at = models.DateTimeField(_("updated at"), default=timezone.now)

    STATUS_CONFIRM = "confirm"
    STATUS_REVIEW = "review"
    STATUS_REJECTED = "rejected"
    STATUS_ACCEPTED = "accepted"
    STATUS_COMPLETED = "completed"

    STATUS_TYPE = (
        (STATUS_CONFIRM, _("Awaiting email confirmation")),
        (STATUS_REVIEW, _("Ready for review")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_ACCEPTED, _("Accepted")),
        (STATUS_COMPLETED, _("Completed")),
    )

    status = models.CharField(
        verbose_name=_("status"), choices=STATUS_TYPE, max_length=20, default="confirm",
    )

    MEMBERSHIP_YEAR = "year"
    MEMBERSHIP_STUDY = "study"

    MEMBERSHIP_LENGTHS = (
        (
            MEMBERSHIP_YEAR,
            _("One year")
            + f" -- €{floatformat(settings.MEMBERSHIP_PRICES['year'], 2)}",
        ),
        (
            MEMBERSHIP_STUDY,
            _("Until graduation")
            + f" -- €{floatformat(settings.MEMBERSHIP_PRICES['study'], 2)}",
        ),
    )

    length = models.CharField(
        verbose_name=_("membership length"), choices=MEMBERSHIP_LENGTHS, max_length=20,
    )

    MEMBERSHIP_TYPES = [
        m for m in Membership.MEMBERSHIP_TYPES if m[0] != Membership.HONORARY
    ]

    contribution = models.DecimalField(
        verbose_name=_("contribution"),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(settings.MEMBERSHIP_PRICES["year"])],
        default=settings.MEMBERSHIP_PRICES["year"],
        blank=False,
        null=False,
    )

    no_references = models.BooleanField(
        verbose_name=_("no references required"), default=False
    )

    membership_type = models.CharField(
        verbose_name=_("membership type"),
        choices=MEMBERSHIP_TYPES,
        max_length=40,
        default=Membership.MEMBER,
    )

    remarks = models.TextField(_("remarks"), blank=True, null=True,)

    payment = models.OneToOneField(
        "payments.Payment",
        related_name="registrations_entry",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    membership = models.OneToOneField(
        "members.Membership", on_delete=models.SET_NULL, blank=True, null=True,
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.status != self.STATUS_ACCEPTED and self.status != self.STATUS_REJECTED:
            self.updated_at = timezone.now()

        if self.membership_type == Membership.BENEFACTOR:
            self.length = self.MEMBERSHIP_YEAR
        else:
            self.contribution = settings.MEMBERSHIP_PRICES[self.length]

        super().save(force_insert, force_update, using, update_fields)

    def clean(self):
        super().clean()
        errors = {}

        if self.contribution is None and self.membership_type == Membership.BENEFACTOR:
            errors.update(
                {"contribution": _("This field is required for benefactors.")}
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        try:
            return self.registration.__str__()
        except Registration.DoesNotExist:
            return self.renewal.__str__()

    class Meta:
        verbose_name = _("entry")
        verbose_name_plural = _("entries")
        permissions = (
            ("review_entries", _("Review registration and renewal entries")),
        )


class Registration(Entry):
    """Describes a new registration for the association."""

    # ---- Personal information -----

    username = models.CharField(
        _("Username"),
        max_length=64,  # This length is lower than Django because of G Suite
        blank=True,
        null=True,
        help_text=_(
            "Enter value to override the auto-generated username "
            "(e.g. if it is not unique)"
        ),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9]{1,64}$",
                message=_(
                    "Please use 64 characters or fewer. Letters and digits only."
                ),
            )
        ],
    )

    first_name = models.CharField(_("First name"), max_length=30, blank=False,)

    last_name = models.CharField(_("Last name"), max_length=200, blank=False,)

    birthday = models.DateField(verbose_name=_("birthday"), blank=False,)

    @property
    def language(self):
        return "en"

    # ---- Contact information -----

    email = models.EmailField(_("Email address"), blank=False,)

    phone_number = models.CharField(
        max_length=20,
        verbose_name=_("phone number"),
        validators=[
            validators.RegexValidator(
                regex=r"^\+?\d+$", message=_("please enter a valid phone number"),
            )
        ],
        blank=True,
        null=True,
    )

    # ---- University information -----

    student_number = models.CharField(
        verbose_name=_("student number"),
        max_length=8,
        validators=[
            validators.RegexValidator(
                regex=r"([Ss]\d{7}|[EZUezu]\d{6,7})",
                message=_("enter a valid student- or e/z/u-number."),
            )
        ],
        help_text=_("With prefix. For example: 's5603249'."),
        blank=True,
        null=True,
    )

    programme = models.CharField(
        max_length=20,
        choices=Profile.PROGRAMME_CHOICES,
        verbose_name=_("study programme"),
        blank=True,
        null=True,
    )

    starting_year = models.IntegerField(
        verbose_name=_("starting year"), blank=True, null=True,
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
        verbose_name=_("street and house number"),
        blank=False,
    )

    address_street2 = models.CharField(
        max_length=100, verbose_name=_("second address line"), blank=True, null=True,
    )

    address_postal_code = models.CharField(
        max_length=10, verbose_name=_("postal code"), blank=False,
    )

    address_city = models.CharField(max_length=40, verbose_name=_("city"), blank=False,)

    address_country = models.CharField(
        max_length=2, choices=countries.EUROPE, verbose_name=_("Country"), null=True,
    )

    # ---- Opt-ins -----

    optin_mailinglist = models.BooleanField(
        verbose_name=_("mailinglist opt-in"), default=False
    )

    optin_birthday = models.BooleanField(
        verbose_name=_("birthday calendar opt-in"), default=False
    )

    # ---- Bank account -----

    direct_debit = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        help_text=_(
            "When the registration is accepted and this checkbox is enabled, a "
            "Thalia Pay payment will be created for this user and the registration "
            "will be completed immediately. This can only be selected if a bank "
            "account is added with direct debit authorisation during registration."
        ),
    )

    initials = models.CharField(
        verbose_name=_("initials"), max_length=20, blank=True, null=True
    )

    iban = IBANField(
        verbose_name=_("IBAN"),
        include_countries=IBAN_SEPA_COUNTRIES,
        blank=True,
        null=True,
    )

    bic = BICField(
        verbose_name=_("BIC"),
        blank=True,
        null=True,
        help_text=_("This field is optional for Dutch bank accounts."),
    )

    signature = models.TextField(verbose_name=_("signature"), blank=True, null=True,)

    def get_full_name(self):
        full_name = "{} {}".format(self.first_name, self.last_name)
        return full_name.strip()

    def clean(self):
        super().clean()
        errors = {}

        if (
            get_user_model().objects.filter(email=self.email).exists()
            or Registration.objects.filter(email=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            errors.update(
                {
                    "email": _(
                        "A user with that email address already exists. "
                        "Login using the existing account and renew the "
                        "membership by visiting the account settings."
                    )
                }
            )

        if self.student_number is not None:
            self.student_number = self.student_number.lower()
            if (
                Profile.objects.filter(student_number=self.student_number).exists()
                or Registration.objects.filter(student_number=self.student_number)
                .exclude(pk=self.pk)
                .exists()
            ):
                errors.update(
                    {
                        "student_number": _(
                            "A user with that student number already exists. "
                            "Login using the existing account and renew the "
                            "membership by visiting the account settings."
                        )
                    }
                )
        elif (
            self.student_number is None
            and self.membership_type != Membership.BENEFACTOR
        ):
            errors.update({"student_number": _("This field is required.")})

        if (
            self.username is not None
            and get_user_model().objects.filter(username=self.username).exists()
        ):
            errors.update({"username": _("A user with that username already exists.")})

        if self.starting_year is None and self.membership_type != Membership.BENEFACTOR:
            errors.update({"starting_year": _("This field is required.")})

        if self.programme is None and self.membership_type != Membership.BENEFACTOR:
            errors.update({"programme": _("This field is required.")})

        if self.direct_debit:
            if not self.iban:
                errors.update(
                    {
                        "iban": _(
                            "This field is required to add a bank account mandate for Thalia Pay."
                        )
                    }
                )

            if not self.initials:
                errors.update(
                    {
                        "initials": _(
                            "This field is required to add a bank account mandate for Thalia Pay."
                        )
                    }
                )

            if not self.signature:
                errors.update(
                    {
                        "signature": _(
                            "This field is required to add a bank account mandate for Thalia Pay."
                        )
                    }
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return "{} {} ({})".format(self.first_name, self.last_name, self.email)

    class Meta:
        verbose_name = _("registration")
        verbose_name_plural = _("registrations")


class Renewal(Entry):
    """Describes a renewal for the association membership."""

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        verbose_name=_("member"),
        blank=False,
        null=False,
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.pk is None:
            self.status = Entry.STATUS_REVIEW
        super().save(force_insert, force_update, using, update_fields)

    def clean(self):
        super().clean()
        errors = {}

        if (
            Renewal.objects.filter(member=self.member, status=Entry.STATUS_REVIEW)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                _("You already have a renewal request queued for review.")
            )

        # Invalid form for study and honorary members
        current_membership = self.member.current_membership
        if current_membership is not None and current_membership.until is None:
            errors.update(
                {
                    "length": _("You currently have an active membership."),
                    "membership_type": _("You currently have an active membership."),
                }
            )

        latest_membership = self.member.latest_membership
        hide_year_choice = not (
            latest_membership is not None
            and latest_membership.until is not None
            and (latest_membership.until - timezone.now().date()).days <= 31
        )

        if self.length == Entry.MEMBERSHIP_YEAR and hide_year_choice:
            errors.update(
                {"length": _("You cannot renew your membership at this moment.")}
            )

        if (
            self.membership_type == Membership.BENEFACTOR
            and self.length == Entry.MEMBERSHIP_STUDY
        ):
            errors.update(
                {
                    "length": _(
                        "Benefactors cannot have a membership "
                        "that lasts their entire study duration."
                    )
                }
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return "{} {} ({})".format(
            self.member.first_name, self.member.last_name, self.member.email
        )

    class Meta:
        verbose_name = _("renewal")
        verbose_name_plural = _("renewals")


class Reference(models.Model):
    """Describes a reference of a member for a potential member."""

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        verbose_name=_("member"),
        blank=False,
        null=False,
    )

    entry = models.ForeignKey(
        "registrations.Entry",
        on_delete=models.CASCADE,
        verbose_name=_("entry"),
        blank=False,
        null=False,
    )

    def __str__(self):
        return f"Reference from {self.member} for {self.entry}"

    class Meta:
        unique_together = ("member", "entry")
