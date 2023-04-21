from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from events.models import Event, EventRegistration, RegistrationInformationField
from events.widgets import FieldsWidget


class RegistrationAdminForm(forms.ModelForm):
    """Custom admin form to add a link to the registration information fields admin."""

    fields = forms.URLField(widget=FieldsWidget, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            if self.instance.event.has_fields:
                self.fields["fields"].initial = reverse(
                    "admin:events_registration_fields", args=[self.instance.pk]
                )
            else:
                self.fields["fields"].widget = self.fields["fields"].hidden_widget()
        except Event.DoesNotExist:
            self.fields["fields"].widget = self.fields["fields"].hidden_widget()

    class Meta:
        fields = "__all__"
        model = EventRegistration


class RegistrationInformationFieldForm(forms.ModelForm):
    """Custom form for the registration information fields that adds an order field."""

    order = forms.IntegerField(label=_("order"), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            event = self.instance.event
            order = event.get_registrationinformationfield_order()
            order_value = list(order).index(self.instance.pk)
            self.fields["order"].initial = order_value
        except Event.DoesNotExist:
            pass

    class Meta:
        fields = "__all__"
        model = RegistrationInformationField
        widgets = {
            "type": forms.Select,
        }


class EventAdminForm(forms.ModelForm):
    def clean(self):
        super().clean()
        self.instance.clean_changes(self.changed_data)

    def clean_organisers(self):
        if (
            self.request.member
            and self.cleaned_data.get("organisers")
            and not (
                self.request.member.get_member_groups()
                .filter(pk__in=self.cleaned_data.get("organisers").values_list("pk"))
                .exists()
            )
        ) and not (
            self.request.user.is_superuser
            or self.request.user.has_perm("events.override_organiser")
        ):
            raise ValidationError(
                _("You cannot remove your own access from this event.")
            )

        if self.cleaned_data.get("organisers").all() == 0:
            raise ValidationError(_("An event must have at least one organiser."))
        return self.cleaned_data.get("organisers")
