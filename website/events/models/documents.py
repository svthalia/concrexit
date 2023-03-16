from django.db import models
from django.utils.translation import gettext_lazy as _
from documents.models import Document


class EventDocument(Document):
    """Describes a document for events."""

    class Meta:
        verbose_name = _("event document")
        verbose_name_plural = _("event documents")
        permissions = (("override_owner", "Can access event document as if owner"),)

    owner = models.ForeignKey(
        "activemembers.MemberGroup",
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
    )

    def save(self, **kwargs):
        self.category = "event"
        super().save(**kwargs)
