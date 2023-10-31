from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from thumbnails.fields import ImageField
from tinymce.models import HTMLField

from utils import countries
from utils.media.services import get_upload_to_function


class Partner(models.Model):
    """Model describing partner."""

    is_active = models.BooleanField(default=False)
    is_main_partner = models.BooleanField(default=False)
    is_local_partner = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    link = models.CharField(max_length=255, blank=True, validators=[URLValidator()])
    company_profile = HTMLField(blank=True)

    logo = ImageField(
        upload_to=get_upload_to_function("partners/logos/"),
        resize_source_to="source_png",
        storage=storages["public"],
    )

    alternate_logo = ImageField(
        upload_to=get_upload_to_function("partners/logos/"),
        resize_source_to="source_png",
        storage=storages["public"],
        blank=True,
        null=True,
        help_text=_(
            "If set, this logo will be shown on the frontpage banner. Please use files with proper transparency."
        ),
    )

    site_header = ImageField(
        upload_to=get_upload_to_function("partners/headers/"),
        resize_source_to="source_png",
        storage=storages["public"],
        null=True,
        blank=True,
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
        max_length=100,
        verbose_name=_("Second address line"),
        blank=True,
        null=True,
    )

    zip_code = models.CharField(
        max_length=12,
    )

    city = models.CharField(max_length=100)

    country = models.CharField(
        max_length=2, choices=countries.EUROPE, verbose_name=_("Country")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orig_logo = self.logo.name if self.logo else None
        self._orig_site_header = self.site_header.name if self.site_header else None

    def delete(self, using=None, keep_parents=False):
        if self.logo.name:
            self.logo.delete()
        if self.site_header.name:
            self.site_header.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        """Save a partner and set main/local partners."""
        if self.is_main_partner:
            self.is_local_partner = False
            self._reset_main_partner()

        super().save(**kwargs)

        if self._orig_logo and self._orig_logo != self.logo.name:
            self.logo.storage.delete(self._orig_logo)
            self._orig_logo = None
        if self._orig_site_header and self._orig_site_header != self.site_header.name:
            self.site_header.storage.delete(self._orig_site_header)
            self._orig_site_header = None

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
    image = ImageField(
        upload_to="partners/images/",
        resize_source_to="source_png",
        storage=storages["public"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orig_image = self.image.name if self.image else None

    def delete(self, using=None, keep_parents=False):
        if self.image.name:
            self.image.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        super().save(**kwargs)

        if self._orig_image and self._orig_image != self.image.name:
            self.image.storage.delete(self._orig_image)
            self._orig_image = None

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
    company_logo = ImageField(
        _("company logo"),
        upload_to="partners/vacancy-logos/",
        resize_source_to="source_png",
        storage=storages["public"],
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
        return f"{self.get_company_name()} — {self.title}"

    def get_absolute_url(self):
        """Return partner or vacancy url."""
        url = reverse("partners:vacancies")
        if self.partner and self.partner.is_active:
            url = reverse("partners:partner", args=(self.partner.slug,))
        return f"{url}#vacancy-{self.pk}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orig_logo = self.company_logo.name if self.company_logo else None

    def delete(self, using=None, keep_parents=False):
        if self.company_logo.name:
            self.company_logo.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        super().save(**kwargs)

        if self._orig_logo and self._orig_logo != self.company_logo.name:
            self.company_logo.storage.delete(self._orig_logo)
            self._orig_logo = None

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
                {
                    "partner": msg,
                    "company_name": msg,
                    "company_logo": msg,
                }
            )

        if errors:
            raise ValidationError(errors)

    class Meta:
        """Meta class for vacancy model."""

        ordering = ["-pk"]
        verbose_name_plural = _("Vacancies")
