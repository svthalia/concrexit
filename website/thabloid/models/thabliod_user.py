from django.db import models
from django.db.models import BooleanField
from django.db.models.expressions import Case, When
from django.utils.translation import gettext_lazy as _

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import queryable_property

from members.models import Member


class Thabloid_user(Member):
    class Meta:
        verbose_name = _("Thabloid user")
        verbose_name_plural = _("Thabloid users")
        proxy = True

    objects = QueryablePropertiesManager()

    @queryable_property(annotation_based=True)
    @classmethod
    def wants_thabloid(cls):
        return Case(
            When(blacklistedthabloiduser__isnull=False, then=False),
            default=True,
            output_field=BooleanField(),
        )

    def allow_thabloid(self):
        """Unmark that the user wants to receive the Thabloid."""
        delted, _ = BlacklistedThabloidUser.objects.filter(thabloid_user=self).delete()
        return delted > 0

    def disallow_thabloid(self):
        """Mark that the user does want to receive the Thabloid."""
        created, _ = BlacklistedThabloidUser.objects.get_or_create(thabloid_user=self)
        return created


class BlacklistedThabloidUser(models.Model):
    class Meta:
        verbose_name = _("Blacklisted Thabloid user")
        verbose_name_plural = _("Blacklisted Thabloid users")

    thabloid_user = models.OneToOneField(
        Thabloid_user,
        on_delete=models.CASCADE,
    )
