from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from tinymce.models import HTMLField

from utils.translation import ModelTranslateMeta, MultilingualField


class Newsletter(models.Model, metaclass=ModelTranslateMeta):
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

    class Meta:
        permissions = (
            ("send_newsletter", "Can send newsletter"),
        )


class NewsletterContent(models.Model, metaclass=ModelTranslateMeta):
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

    class Meta:
        #abstract = True
        order_with_respect_to = 'newsletter'


class NewsletterItem(NewsletterContent):
    pass


class NewsletterEvent(NewsletterContent):
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
        super().clean()
        if self.end_datetime < self.start_datetime:
            raise ValidationError({
                'end': _("Can't have an event travel back in time")
            })
