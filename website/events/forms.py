from django import forms
from django.utils.translation import gettext_lazy as _

from .models import RegistrationInformationField


class FieldsForm(forms.Form):
    """Form that outputs the correct widgets for the information fields."""

    def __init__(self, *args, **kwargs):
        self.information_fields = kwargs.pop("fields")
        super().__init__(*args, **kwargs)

        for key, field in self.information_fields.items():
            field_type = field["type"]

            if field_type == RegistrationInformationField.BOOLEAN_FIELD:
                self.fields[key] = forms.BooleanField(required=False)
            elif field_type == RegistrationInformationField.INTEGER_FIELD:
                self.fields[key] = forms.IntegerField(required=field["required"])
            elif field_type == RegistrationInformationField.TEXT_FIELD:
                self.fields[key] = forms.CharField(required=field["required"])

            self.fields[key].label = field["label"]
            self.fields[key].help_text = field["description"]
            self.fields[key].initial = field["value"]

    def field_values(self):
        for key in self.information_fields:
            yield key, self.cleaned_data[key]


class EventMessageForm(forms.Form):
    """Form that outputs a widget to get info to send a push notification."""

    title = forms.CharField(label=_("title"), max_length=150)
    body = forms.CharField(label=_("body"), widget=forms.Textarea)
    url = forms.CharField(
        max_length=256,
        required=False,
        help_text=_("The notification opens to the event by default."),
    )
