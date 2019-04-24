"""The models defined by the newsletters package"""
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from tinymce.models import HTMLField

from utils.translation import ModelTranslateMeta, MultilingualField


class Newsletter(models.Model, metaclass=ModelTranslateMeta):
    """Describes a newsletter"""

    title = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('Title'),
        help_text=_('The title is used for the email subject.'),
        blank=False,
    )

    date = models.DateField(
        verbose_name=_('Date'),
        help_text=_('This date is used to extract the week of this '
                    'newsletter, best scenario:'
                    'always use the monday of the week the newsletter is '
                    'for. If you leave it empty no week is shown.'),
        blank=True,
        null=True
    )

    send_date = models.DateTimeField(
        verbose_name=_('Send date'),
        blank=True,
        null=True,
    )

    description = MultilingualField(
        HTMLField,
        verbose_name=_('Introduction'),
        help_text=_('This is the text that starts the newsletter. It always '
                    'begins with "Dear members" and you can append '
                    'whatever you want.'),
        blank=False,
    )

    sent = models.BooleanField(
        default=False
    )

    def get_absolute_url(self):
        return reverse('newsletters:preview', args=(self.pk,))

    def clean(self):
        super().clean()

        errors = {}
        url = 'admin/newsletters/'
        if url in self.description_nl:
            errors.update({
                'description_nl': _('Please make sure all urls are absolute '
                                    'and contain http(s)://.')
            })
        if url in self.description_en:
            errors.update({
                'description_en': _('Please make sure all urls are absolute '
                                    'and contain http(s)://.')
            })
        if self.send_date and self.send_date <= timezone.now():
            errors.update({
                'send_date': _('Please make sure the send date is '
                               'not in the past.')
            })

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        permissions = (
            ("send_newsletter", "Can send newsletter"),
        )

    def __str__(self):
        return self.title


class NewsletterContent(models.Model, metaclass=ModelTranslateMeta):
    """Describes one piece of basic content of a newsletter"""

    title = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('Title'),
        blank=False,
        null=False,
    )

    description = MultilingualField(
        HTMLField,
        verbose_name=_('Description'),
        blank=False,
        null=False,
    )

    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)

    def clean(self):
        super().clean()

        errors = {}
        url = 'admin/newsletters/'
        if url in self.description_nl:
            errors.update({
                'description_nl': _('Please make sure all urls are absolute '
                                    'and contain http(s)://.')
            })
        if url in self.description_en:
            errors.update({
                'description_en': _('Please make sure all urls are absolute '
                                    'and contain http(s)://.')
            })

        if errors:
            raise ValidationError(errors)

    class Meta:
        order_with_respect_to = 'newsletter'

    def __str__(self):
        return self.title


class NewsletterItem(NewsletterContent):
    """Describes one piece of text content of a newsletter"""
    pass


class NewsletterEvent(NewsletterContent):
    """Describes one piece of event content of a newsletter"""
    what = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('What'),
        blank=False,
        null=False,
    )

    where = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('Where'),
        blank=False,
        null=False,
    )

    start_datetime = models.DateTimeField(
        verbose_name=_('Start date and time'),
        blank=False,
        null=False,
    )

    end_datetime = models.DateTimeField(
        verbose_name=_('End date and time'),
        blank=False,
        null=False,
    )

    show_costs_warning = models.BooleanField(
        verbose_name=_('Show warnings about costs'),
        default=True
    )

    price = models.DecimalField(
        verbose_name=_('Price (in Euro)'),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        default=None,
    )

    penalty_costs = models.DecimalField(
        verbose_name=_('Costs (in Euro)'),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        default=None,
        help_text=_('This is the price that a member has to '
                    'pay when he/she did not show up.'),
    )

    def clean(self):
        """Make sure that the event end date is after the start date"""
        super().clean()
        if (self.end_datetime is not None and
                self.start_datetime is not None and
                self.end_datetime < self.start_datetime):
            raise ValidationError({
                'end_datetime': _("Can't have an event travel back in time")
            })
