from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    """Describes a base document."""

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    DOCUMENT_CATEGORIES = (
        ("annual", _("Annual document")),
        ("association", _("Association document")),
        ("event", _("Event document")),
        ("minutes", _("Minutes")),
        ("misc", _("Miscellaneous document")),
    )

    name = models.CharField(verbose_name=_("name"), max_length=200)

    created = models.DateTimeField(verbose_name=_("created"), auto_now_add=True,)

    last_updated = models.DateTimeField(verbose_name=_("last updated"), auto_now=True)

    category = models.CharField(
        max_length=40,
        choices=DOCUMENT_CATEGORIES,
        verbose_name=_("category"),
        default="misc",
    )

    file = models.FileField(
        verbose_name=_("file"),
        upload_to="documents/",
        validators=[FileExtensionValidator(["txt", "pdf", "jpg", "jpeg", "png"])],
    )

    members_only = models.BooleanField(verbose_name=_("members only"), default=False)

    def get_absolute_url(self):
        return reverse("documents:document", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} ({self.created.date()})"


class AnnualDocument(Document):
    """Describes an annual document."""

    class Meta:
        verbose_name = _("Annual document")
        verbose_name_plural = _("Annual documents")
        unique_together = ("subcategory", "year")

    SUBCATEGORIES = (
        ("report", _("Annual report")),
        ("financial", _("Financial report")),
        ("policy", _("Policy document")),
    )

    subcategory = models.CharField(
        max_length=40,
        choices=SUBCATEGORIES,
        verbose_name=_("category"),
        default="report",
    )

    year = models.IntegerField(
        verbose_name=_("year"), validators=[MinValueValidator(1990)],
    )

    def save(self, **kwargs):
        self.category = "annual"
        if self.subcategory == "report":
            self.name = "Annual report %d" % self.year
        elif self.subcategory == "financial":
            self.name = "Financial report %d" % self.year
        else:
            self.name = "Policy document %d" % self.year
        super().save(**kwargs)


class AssociationDocumentManager(models.Manager):
    """Custom manager to filter for association documents."""

    def get_queryset(self):
        return super().get_queryset().filter(category="association")


class AssociationDocument(Document):
    """Describes an association document."""

    class Meta:
        verbose_name = _("Miscellaneous association document")
        verbose_name_plural = _("Miscellaneous association documents")
        proxy = True

    objects = AssociationDocumentManager()

    def save(self, **kwargs):
        self.category = "association"
        super().save(**kwargs)


class EventDocument(Document):
    """Describes a document for events."""

    class Meta:
        verbose_name = _("event document")
        verbose_name_plural = _("event documents")
        permissions = (("override_owner", "Can access event document as if owner"),)

    owner = models.ForeignKey(
        "activemembers.MemberGroup", verbose_name=_("owner"), on_delete=models.CASCADE,
    )

    def save(self, **kwargs):
        self.category = "event"
        super().save(**kwargs)


class MiscellaneousDocumentManager(models.Manager):
    """Custom manager to filter for misc documents."""

    def get_queryset(self):
        return super().get_queryset().filter(category="misc")


class MiscellaneousDocument(Document):
    """Describes a miscellaneous document."""

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Miscellaneous document")
        verbose_name_plural = _("Miscellaneous documents")
        proxy = True

    objects = MiscellaneousDocumentManager()

    def save(self, **kwargs):
        self.category = "misc"
        super().save(**kwargs)


class GeneralMeeting(models.Model):
    """Describes a general meeting."""

    class Meta:
        verbose_name = _("General meeting")
        verbose_name_plural = _("General meetings")
        ordering = ["datetime"]

    documents = models.ManyToManyField(
        Document, verbose_name=_("documents"), blank=True,
    )

    datetime = models.DateTimeField(verbose_name=_("datetime"),)

    location = models.CharField(verbose_name=_("location"), max_length=200)

    def __str__(self):
        return timezone.localtime(self.datetime).strftime("%Y-%m-%d")


class Minutes(Document):
    """Describes a minutes document."""

    class Meta:
        verbose_name = _("Minutes")
        verbose_name_plural = _("Minutes")

    meeting = models.OneToOneField(
        GeneralMeeting, blank=True, null=True, on_delete=models.CASCADE
    )

    def save(self, **kwargs):
        self.category = "minutes"
        self.name = "Minutes %s" % str(self.meeting.datetime.date())
        super().save(**kwargs)
