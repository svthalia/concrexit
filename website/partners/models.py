from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from tinymce.models import HTMLField

from utils import countries


class Partner(models.Model):
    """Model describing partner."""

    is_active = models.BooleanField(default=False)
    is_main_partner = models.BooleanField(default=False)
    is_local_partner = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    link = models.CharField(max_length=255, blank=True, validators=[URLValidator()])
    company_profile = HTMLField(blank=True)
    logo = models.ImageField(upload_to="public/partners/logos/")
    site_header = models.ImageField(
        upload_to="public/partners/headers/", null=True, blank=True
    )

    address = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=(
                    r"^([1-9][e][\s])*([ëéÉËa-zA-Z]"
                    r"+(([\.][\s])|([\s]))?)+[1-9][0-9]"
                    r"*(([-][1-9][0-9]*)|([\s]?[ëéÉËa-zA-Z]+))?$"
                ),
                message=_("Enter a valid address"),
            )
        ],
    )

    address2 = models.CharField(
        max_length=100, verbose_name=_("Second address line"), blank=True, null=True,
    )

    zip_code = models.CharField(max_length=12,)

    city = models.CharField(max_length=100)

    country = models.CharField(
        max_length=2, choices=countries.EUROPE, verbose_name=_("Country")
    )

    def save(self, **kwargs):
        """Save a partner and set main/local partners."""
        if self.is_main_partner:
            self.is_local_partner = False
            self._reset_main_partner()
        if self.is_local_partner:
            self._reset_local_partner()

        super().save(**kwargs)

    def _reset_main_partner(self):
        """Reset the main partner status.

        If this partner is not main partner,
        remove the main partner status from the main partner.
        """
        try:
            current_main_partner = Partner.objects.get(is_main_partner=True)
            if self != current_main_partner:
                current_main_partner.is_main_partner = False
                current_main_partner.save()
        except Partner.DoesNotExist:
            pass

    def _reset_local_partner(self):
        """Reset the local partner status.

        If this partner is not local partner,
        remove the local partner status from the local partner.
        """
        try:
            current_local_partner = Partner.objects.get(is_local_partner=True)
            if self != current_local_partner:
                current_local_partner.is_local_partner = False
                current_local_partner.save()
        except Partner.DoesNotExist:
            pass

    def __str__(self):
        """Return the name of the partner."""
        return str(self.name)

    def get_absolute_url(self):
        """Return the url of the partner page."""
        return reverse("partners:partner", args=(self.slug,))

    class Meta:
        """Meta class for partner model."""

        ordering = ("name",)


class PartnerImage(models.Model):
    """Model to save partner image."""

    partner = models.ForeignKey(
        Partner, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="public/partners/images/")

    def __str__(self):
        """Return string representation of partner name."""
        return gettext("image of {}").format(self.partner.name)


class VacancyCategory(models.Model):
    """Model describing vacancy categories."""

    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)

    def __str__(self):
        """Return the category name."""
        return str(self.name)

    class Meta:
        """Meta class for vacancy category model."""

        verbose_name_plural = _("Vacancy Categories")


class Vacancy(models.Model):
    """Model describing vacancies."""

    title = models.CharField(_("title"), max_length=255)
    description = HTMLField(_("description"))
    link = models.CharField(
        _("link"), max_length=255, blank=True, validators=[URLValidator()]
    )
    location = models.CharField(_("location"), max_length=255, null=True, blank=True)
    keywords = models.TextField(
        _("keywords"),
        default="",
        help_text="Comma separated list of keywords, for example: "
        "Django,Python,Concrexit",
        blank=True,
    )

    partner = models.ForeignKey(
        Partner,
        verbose_name=_("partner"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_(
            "When you use a partner, the company name and logo "
            "below will not be used."
        ),
    )

    company_name = models.CharField(_("company name"), max_length=255, blank=True)
    company_logo = models.ImageField(
        _("company logo"),
        upload_to="public/partners/vacancy-logos/",
        null=True,
        blank=True,
    )

    categories = models.ManyToManyField(VacancyCategory, blank=True)

    def get_company_name(self):
        """Return company or partner name."""
        if self.partner:
            return self.partner.name
        return self.company_name

    def get_company_logo(self):
        """Return company or partner logo."""
        if self.partner:
            return self.partner.logo
        return self.company_logo

    def __str__(self):
        """Return vacancy partner or company and title."""
        return "{} — {}".format(self.get_company_name(), self.title)

    def get_absolute_url(self):
        """Return partner or vacancy url."""
        url = reverse("partners:vacancies")
        if self.partner:
            url = reverse("partners:partner", args=(self.partner.slug,))
        return "{}#vacancy-{}".format(url, self.pk)

    def clean(self):
        """Validate the vacancy."""
        super().clean()
        errors = {}

        msg = _("If no partner is used then both a company name and logo are required.")
        if not self.partner and self.company_name and not self.company_logo:
            errors.update({"company_logo": msg})
        if not self.partner and not self.company_name and self.company_logo:
            errors.update({"company_name": msg})

        msg = _("Either select a partner or provide a company name and logo.")
        if self.partner and (self.company_name or self.company_logo):
            errors.update({"partner": msg})
            if self.company_name:
                errors.update({"company_name": msg})
            if self.company_logo:
                errors.update({"company_logo": msg})
        if not self.partner and not self.company_name and not self.company_logo:
            errors.update(
                {"partner": msg, "company_name": msg, "company_logo": msg,}
            )

        if errors:
            raise ValidationError(errors)

    class Meta:
        """Meta class for vacancy model."""

        ordering = ["-pk"]
        verbose_name_plural = _("Vacancies")


class PartnerEvent(models.Model):
    """Model describing partner event."""

    partner = models.ForeignKey(
        Partner,
        verbose_name=_("partner"),
        on_delete=models.CASCADE,
        related_name="events",
        blank=True,
        null=True,
    )

    other_partner = models.CharField(max_length=255, blank=True)

    title = models.CharField(_("title"), max_length=100)

    description = models.TextField(_("description"))

    location = models.CharField(_("location"), max_length=255,)

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    url = models.URLField(_("website"))

    published = models.BooleanField(_("published"), default=False)

    def clean(self):
        """Validate the partner event."""
        super().clean()
        errors = {}
        if (not self.partner and not self.other_partner) or (
            self.partner and self.other_partner
        ):
            errors.update(
                {
                    "partner": _("Please select or enter a partner for this event."),
                    "other_partner": _(
                        "Please select or enter a partner for this event."
                    ),
                }
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Return the event title."""
        return str(self.title)
