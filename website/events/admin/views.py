import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.views import View
from django.views.generic import DetailView, FormView

import qrcode

from events import services
from events.decorators import organiser_only
from events.exceptions import RegistrationError
from events.forms import EventMessageForm, FieldsForm
from events.models import Event, EventRegistration
from payments.models import Payment
from pushnotifications.models import Category, Message


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class EventAdminDetails(DetailView, PermissionRequiredMixin):
    """Render an overview of registrations for the specified event."""

    template_name = "events/admin/details.html"
    model = Event
    context_object_name = "event"
    permission_required = "events.change_event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({"payment": Payment, "has_permission": True, "site_url": "/"})

        return context


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class RegistrationAdminFields(FormView):
    """Render a form that allows the user to change the details of their registration.

    The user should be authenticated.
    """

    form_class = FieldsForm
    template_name = "admin/change_form.html"
    registration = None
    admin = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "add": False,
                "change": True,
                "has_view_permission": True,
                "has_add_permission": False,
                "has_change_permission": self.request.user.has_perms(
                    "events.change_eventregistration"
                ),
                "has_delete_permission": False,
                "has_editable_inline_admin_formsets": False,
                "app_label": "events",
                "opts": self.registration._meta,
                "is_popup": False,
                "save_as": False,
                "save_on_top": False,
                "original": self.registration,
                "obj_id": self.registration.pk,
                "title": _("Change registration fields"),
                "adminform": helpers.AdminForm(
                    context["form"],
                    ((None, {"fields": context["form"].fields.keys()}),),
                    {},
                ),
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fields"] = services.registration_fields(
            self.request, registration=self.registration
        )
        return kwargs

    def form_valid(self, form):
        values = form.field_values()
        try:
            services.update_registration(
                registration=self.registration,
                field_values=values,
                actor=self.request.user,
            )
            messages.success(self.request, _("Registration successfully saved."))
            if "_save" in self.request.POST:
                return redirect(
                    "admin:events_eventregistration_change", self.registration.pk
                )
        except RegistrationError as e:
            messages.error(self.request, e)
        return self.render_to_response(self.get_context_data(form=form))

    def dispatch(self, request, *args, **kwargs):
        self.registration = get_object_or_404(
            EventRegistration, pk=self.kwargs["registration"]
        )
        try:
            if self.registration.event.has_fields:
                return super().dispatch(request, *args, **kwargs)
        except RegistrationError:
            pass
        return redirect("admin:events_eventregistration_change", self.registration.pk)


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class EventMessage(FormView):
    """Renders a form that allows the user to create a push notification for all users registers to the event."""

    form_class = EventMessageForm
    template_name = "events/admin/message_form.html"
    admin = None
    event = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "add": False,
                "change": True,
                "has_view_permission": True,
                "has_add_permission": False,
                "has_change_permission": self.request.user.has_perms(
                    "events.change_event"
                ),
                "has_delete_permission": False,
                "has_editable_inline_admin_formsets": False,
                "app_label": "events",
                "opts": self.event._meta,
                "is_popup": False,
                "save_as": False,
                "save_on_top": False,
                "original": self.event,
                "obj_id": self.event.pk,
                "title": _("Send push notification"),
                "adminform": helpers.AdminForm(
                    context["form"],
                    ((None, {"fields": context["form"].fields.keys()}),),
                    {},
                ),
            }
        )
        return context

    def form_valid(self, form):
        values = form.cleaned_data
        if not values["url"]:
            values["url"] = settings.BASE_URL + self.event.get_absolute_url()
        message = Message(
            title=values["title"],
            body=values["body"],
            url=values["url"],
            category=Category.objects.get(key=Category.EVENT),
        )
        message.save()
        message.users.set([r.member for r in self.event.participants if r.member])
        message.send()

        messages.success(self.request, _("Message sent successfully."))
        if "_save" in self.request.POST:
            return redirect("admin:events_event_details", self.event.pk)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)


# todo: export using import-export library
@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class EventRegistrationsExport(View, PermissionRequiredMixin):
    """View to export registrations."""

    template_name = "events/admin/details.html"
    permission_required = "events.change_event"

    def get(self, request, pk):
        """Export the registration of a specified event.

        :param request: the request object
        :param pk: the primary key of the event
        :return: A CSV containing all registrations for the event
        """
        event = get_object_or_404(Event, pk=pk)
        extra_fields = event.registrationinformationfield_set.all()
        registrations = event.eventregistration_set.all()

        header_fields = (
            [
                _("Name"),
                _("Email"),
                _("Paid"),
                _("Present"),
                _("Status"),
                _("Phone number"),
            ]
            + [field.name for field in extra_fields]
            + [_("Date"), _("Date cancelled")]
        )

        rows = []
        if event.price == 0:
            header_fields.remove(_("Paid"))
        for registration in registrations:
            if registration.member:
                name = registration.member.get_full_name()
            else:
                name = registration.name
            status = pgettext_lazy("registration status", "registered").capitalize()
            cancelled = None
            if registration.date_cancelled:
                if registration.is_late_cancellation():
                    status = pgettext_lazy(
                        "registration status", "late cancellation"
                    ).capitalize()
                else:
                    status = pgettext_lazy(
                        "registration status", "cancelled"
                    ).capitalize()
                cancelled = timezone.localtime(registration.date_cancelled)

            elif registration.queue_position:
                status = pgettext_lazy("registration status", "waiting")
            data = {
                _("Name"): name,
                _("Date"): timezone.localtime(registration.date),
                _("Present"): _("Yes") if registration.present else "",
                _("Phone number"): (
                    registration.phone_number if registration.phone_number else ""
                ),
                _("Email"): (registration.email if registration.email else ""),
                _("Status"): status,
                _("Date cancelled"): cancelled,
            }
            if event.price > 0:
                if registration.is_paid():
                    data[_("Paid")] = registration.payment.get_type_display()
                else:
                    data[_("Paid")] = _("No")

            data.update(
                {
                    field["field"].name: field["value"]
                    for field in registration.information_fields
                }
            )
            rows.append(data)

        response = HttpResponse(content_type="text/csv")
        writer = csv.DictWriter(response, header_fields)
        writer.writeheader()

        rows = sorted(
            rows,
            key=lambda row: (
                row[_("Status")]
                == pgettext_lazy(
                    "registration status", "late cancellation"
                ).capitalize(),
                row[_("Date")],
            ),
            reverse=True,
        )

        for row in rows:
            writer.writerow(row)

        response[
            "Content-Disposition"
        ] = f'attachment; filename="{slugify(event.title)}.csv"'
        return response


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class EventMarkPresentQR(View):
    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        image = qrcode.make(event.mark_present_url)

        response = HttpResponse(content_type="image/png")
        image.save(response, "PNG")

        return response
