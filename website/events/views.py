"""Views provided by the events package"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, TemplateView, FormView

from events import services
from events.exceptions import RegistrationError
from payments.models import Payment
from .forms import FieldsForm
from .models import Event, EventRegistration


class EventIndex(TemplateView):
    """
    Renders the events calendar overview
    """

    template_name = "events/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        upcoming_activity = (
            Event.objects.filter(published=True, end__gte=timezone.now())
            .order_by("end")
            .first()
        )
        context["upcoming_activity"] = upcoming_activity

        return context


class EventDetail(DetailView):
    """
    Renders a single event detail page
    """

    model = Event
    queryset = Event.objects.filter(published=True)
    template_name = "events/event.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["payment_method_tpay"] = Payment.TPAY

        event = context["event"]
        if event.max_participants:
            perc = 100.0 * len(event.participants) / event.max_participants
            context["registration_percentage"] = perc

        try:
            context["registration"] = EventRegistration.objects.get(
                event=event, member=self.request.member
            )
        except (EventRegistration.DoesNotExist, TypeError):
            pass

        context["permissions"] = services.event_permissions(self.request.member, event)

        context["date_now"] = timezone.now()

        context["slide_size"] = settings.THUMBNAIL_SIZES["slide"]

        return context


class AlumniEventsView(TemplateView):
    """
    Renders the alumni events page
    """

    template_name = "events/alumni.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        events = Event.objects.filter(
            published=True, category=Event.CATEGORY_ALUMNI, end__gte=timezone.now()
        ).order_by("end")[:3]
        context["events"] = events

        return context


@method_decorator(login_required, name="dispatch")
class EventRegisterView(View):
    """
    Defines a view that allows the user to register for an event using a POST
    request. The user should be authenticated.
    """

    def get(self, request, *args, **kwargs):
        return redirect("events:event", pk=kwargs["pk"])

    def post(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        try:
            services.create_registration(request.member, event)

            if event.has_fields():
                return redirect("events:registration", event.pk)

            messages.success(request, _("Registration successful."))
        except RegistrationError as e:
            messages.error(request, e)

        return redirect(event)


@method_decorator(login_required, name="dispatch")
class EventCancelView(View):
    """
    Defines a view that allows the user to cancel their event registration
    using a POSt request. The user should be authenticated.
    """

    def get(self, request, *args, **kwargs):
        return redirect("events:event", pk=kwargs["pk"])

    def post(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        try:
            services.cancel_registration(request.member, event)
            messages.success(request, _("Registration successfully cancelled."))
        except RegistrationError as e:
            messages.error(request, e)

        return redirect(event)


@method_decorator(login_required, name="dispatch")
class RegistrationView(FormView):
    """
    Renders a form that allows the user to change the details of their
    registration. The user should be authenticated.
    """

    form_class = FieldsForm
    template_name = "events/registration.html"
    event = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fields"] = services.registration_fields(
            self.request, self.request.member, self.event
        )
        return kwargs

    def form_valid(self, form):
        values = form.field_values()
        try:
            services.update_registration(
                self.request.member, self.event, field_values=values
            )
            messages.success(self.request, _("Registration successfully saved."))
            return redirect(self.event)
        except RegistrationError as e:
            messages.error(self.request, e)
            return self.render_to_response(self.get_context_data(form=form))

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs["pk"])
        try:
            if self.event.has_fields():
                return super().dispatch(request, *args, **kwargs)
        except RegistrationError:
            pass
        return redirect(self.event)
