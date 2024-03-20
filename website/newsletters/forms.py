"""The forms defined by the newsletters package."""

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils.translation import gettext_lazy as _

from events.models import Event
from thaliawebsite import settings

from .models import Newsletter, NewsletterEvent


class NewsletterEventForm(forms.ModelForm):
    """Custom ModelForm for the NewsletterEvent model to add the order field and javascript for automatic field filling."""

    class Meta:
        fields = (
            "order",
            "title",
            "url",
            "description",
            "where",
            "start_datetime",
            "end_datetime",
            "show_costs_warning",
            "price",
            "penalty_costs",
        )
        model = NewsletterEvent

    class Media:
        js = (
            "js/js.cookie.min.js",
            "admin/newsletters/js/forms.js",
        )


class NewsletterImportEventForm(forms.Form):
    event_start = forms.DateField(required=False, widget=AdminDateWidget())
    event_end = forms.DateField(required=False, widget=AdminDateWidget())

    registration_start = forms.DateField(required=False, widget=AdminDateWidget())
    registration_end = forms.DateField(required=False, widget=AdminDateWidget())

    remove_existing = forms.BooleanField(required=False, initial=False)

    sort_by = forms.ChoiceField(
        choices=(
            ("start", _("Event start date")),
            ("registration", _("Registrations open date")),
        ),
        required=True,
    )

    def import_events(self, newsletter: Newsletter):
        """Import events from the database into the newsletter."""
        if self.cleaned_data["remove_existing"]:
            NewsletterEvent.objects.filter(newsletter=newsletter).delete()

        events = Event.objects.filter(published=True)

        if self.cleaned_data["event_start"] and self.cleaned_data["registration_start"]:
            events = events.filter(
                start__date__lte=self.cleaned_data["event_end"],
                start__date__gte=self.cleaned_data["event_start"],
                registration_start__date__gte=self.cleaned_data["registration_start"],
                registration_start__date__lte=self.cleaned_data["registration_end"],
            )
        elif self.cleaned_data["event_start"]:
            events = events.filter(
                start__date__gte=self.cleaned_data["event_start"],
                start__date__lte=self.cleaned_data["event_end"],
            )
        elif self.cleaned_data["registration_start"]:
            events = events.filter(
                registration_start__date__gte=self.cleaned_data["registration_start"],
                registration_start__date__lte=self.cleaned_data["registration_end"],
            )

        if self.cleaned_data["sort_by"] == "start":
            events = events.order_by("start")
        elif self.cleaned_data["sort_by"] == "registration":
            events = events.order_by("registration_start")

        max_order = (
            NewsletterEvent.objects.filter(newsletter=newsletter)
            .order_by("-order")
            .first()
        )
        max_order = max_order.order if max_order else 0

        for i, event in enumerate(events, start=max_order + 1):
            NewsletterEvent.objects.create(
                newsletter=newsletter,
                order=i,
                title=event.title,
                url=settings.BASE_URL + event.get_absolute_url(),
                description=event.description,
                where=event.location,
                start_datetime=event.start,
                end_datetime=event.end,
                show_costs_warning=event.fine > 0,
                price=event.price,
                penalty_costs=event.fine,
            )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("event_start") is not None
            and cleaned_data.get("event_end") is None
        ):
            self.add_error(
                "event_end", _("This field is required if you specify a start date.")
            )
        if (
            cleaned_data.get("event_end") is not None
            and cleaned_data.get("event_start") is None
        ):
            self.add_error(
                "event_start", _("This field is required if you specify an end date.")
            )
        if (
            cleaned_data.get("registration_start") is not None
            and cleaned_data.get("registration_end") is None
        ):
            self.add_error(
                "registration_end",
                _("This field is required if you specify a start date."),
            )
        if (
            cleaned_data.get("registration_end") is not None
            and cleaned_data.get("registration_start") is None
        ):
            self.add_error(
                "registration_start",
                _("This field is required if you specify an end date."),
            )

        if cleaned_data.get("event_start") is not None and (
            cleaned_data["event_start"] > cleaned_data["event_end"]
        ):
            self.add_error("event_end", _("Range must end after it starts."))
        if cleaned_data.get("registration_start") is not None and (
            cleaned_data["registration_start"] > cleaned_data["registration_end"]
        ):
            self.add_error("registration_end", _("Range must end after it starts."))

        if cleaned_data.get("event_start") is None and cleaned_data.get(
            "registration_start"
        ):
            self.add_error(
                None,
                _("Please specify which events you want to add to the newsletter."),
            )

        return cleaned_data
