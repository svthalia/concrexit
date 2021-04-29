"""The forms defined by the newsletters package."""
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Event
from .models import NewsletterEvent


class NewsletterEventForm(forms.ModelForm):
    """Custom ModelForm for the NewsletterEvent model to add the order field and javascript for automatic field filling."""

    event = forms.ChoiceField(label=_("Event"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["event"].choices = [(None, "-----")] + [
            (e.pk, e.title)
            for e in Event.objects.filter(published=True, start__gt=timezone.now())
        ]
        self.fields["event"].required = False

    class Meta:
        fields = (
            "order",
            "event",
            "title_en",
            "url",
            "description_en",
            "where_en",
            "start_datetime",
            "end_datetime",
            "show_costs_warning",
            "price",
            "penalty_costs",
        )
        model = NewsletterEvent

    class Media:
        js = (
            "js/js.cookie.js",
            "admin/newsletters/js/forms.js",
        )
