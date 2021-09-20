from datetime import timedelta

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.reverse import reverse

from events import services
from events.models import Event
from thaliawebsite.api.calendarjs.serializers import CalenderJSSerializer


class EventsCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse("events:event", kwargs={"pk": instance.id})

    def _class_names(self, instance):
        if self.context["member"] and services.is_user_registered(
            self.context["member"], instance
        ):
            if services.user_registration_pending(self.context["member"], instance):
                return ["regular-event-pending-registration"]
            else:
                return ["regular-event-has-registration"]
        elif (not instance.registration_required) or instance.registration_allowed:
            return ["regular-event-registration-open"]
        else:
            # I think this handles the case that registration is needed, but not yet possible
            return ["regular-event-registration-closed"]

    def _registration_info(self, instance: Event):
        if self.context["member"] and services.is_user_registered(
            self.context["member"], instance
        ):
            queue_pos = services.user_registration_pending(
                self.context["member"], instance
            )
            if isinstance(queue_pos, int):
                return _("In waiting list at position {queue_pos}").format(
                    queue_pos=queue_pos
                )
            else:
                return _("You are registered for this event")
        elif instance.optional_registration_allowed:
            return _("You can optionally register for this event")
        elif instance.reached_participants_limit:
            return _("You can put yourself on the waiting list for this event")
        elif instance.registration_allowed:
            return _("You can register for this event")
        elif instance.registration_end:
            now = timezone.now()
            if instance.registration_end < now:
                return _("Registrations have been closed")
            elif instance.registration_end <= now + timedelta(days=2):
                return _("You can register {at_time}").format(
                    at_time=naturaltime(instance.registration_end)
                )
            else:
                return _("You can register on {date}").format(
                    date=date(instance.registration_end)
                )


class UnpublishedEventsCalenderJSSerializer(CalenderJSSerializer):
    """See CalenderJSSerializer, customised classes."""

    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _class_names(self, instance):
        return ["unpublished-event"]

    def _url(self, instance):
        return reverse("admin:events_event_details", kwargs={"pk": instance.id})

    def _registration_info(self, instance):
        return "Unpublished event"
