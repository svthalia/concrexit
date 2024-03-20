"""The forms defined by the newsletters package."""

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Event
from thaliawebsite import settings

from .models import Newsletter, NewsletterEvent


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

        (event_start, event_end, registration_start, registration_end) = (
            self.cleaned_data["event_start"],
            self.cleaned_data["event_end"],
            self.cleaned_data["registration_start"],
            self.cleaned_data["registration_end"],
        )

        events = Event.objects.filter(published=True)

        if event_start and registration_start:
            events = events.filter(
                Q(
                    registration_start__date__gte=registration_start,
                    registration_start__date__lte=registration_end,
                )
                | Q(
                    start__date__lte=event_end,
                    start__date__gte=event_start,
                )
            )
        elif event_start:
            events = events.filter(
                start__date__gte=event_start,
                start__date__lte=event_end,
            )
        elif registration_start:
            events = events.filter(
                registration_start__date__gte=registration_start,
                registration_start__date__lte=registration_end,
            )
        else:
            raise forms.ValidationError(
                _("Please specify which events you want to add to the newsletter.")
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
        data = super().clean()
        (event_start, event_end, registration_start, registration_end) = (
            data.get("event_start"),
            data.get("event_end"),
            data.get("registration_start"),
            data.get("registration_end"),
        )
        if event_start is not None and event_end is None:
            self.add_error(
                "event_end", _("This field is required if you specify a start date.")
            )
        if event_end is not None and event_start is None:
            self.add_error(
                "event_start", _("This field is required if you specify an end date.")
            )
        if registration_start is not None and registration_end is None:
            self.add_error(
                "registration_end",
                _("This field is required if you specify a start date."),
            )
        if registration_end is not None and registration_start is None:
            self.add_error(
                "registration_start",
                _("This field is required if you specify an end date."),
            )

        if event_start is not None and (event_start > event_end):
            self.add_error("event_end", _("Range must end after it starts."))
        if registration_start is not None and (registration_start > registration_end):
            self.add_error("registration_end", _("Range must end after it starts."))

        if event_start is None and registration_start is None:
            self.add_error(
                "event_start",
                _("Please specify which events you want to add to the newsletter."),
            )
            self.add_error(
                "registration_start",
                _("Please specify which events you want to add to the newsletter."),
            )

        return data
