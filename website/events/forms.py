from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .models import RegistrationInformationField, Event, Registration
from .widgets import FieldsWidget


class RegistrationAdminForm(forms.ModelForm):
    """
    Custom admin form to add a link to the registration information
    fields admin
    """
    fields = forms.URLField(widget=FieldsWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.event.has_fields():
            self.fields['fields'].initial = (
                reverse('admin:events_registration_fields',
                        args=[self.instance.pk]))
        else:
            self.fields['fields'].widget = self.fields[
                'fields'].hidden_widget()

    class Meta:
        fields = '__all__'
        model = Registration


class RegistrationInformationFieldForm(forms.ModelForm):
    """
    Custom form for the registration information fields
    that adds an order field
    """
    order = forms.IntegerField(label=_('order'), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            event = self.instance.event
            order = event.get_registrationinformationfield_order()
            order_value = list(order).index(self.instance.pk)
            self.fields['order'].initial = order_value
        except Event.DoesNotExist:
            pass

    class Meta:
        fields = '__all__'
        model = RegistrationInformationField
        widgets = {
            'type': forms.Select,
        }


class FieldsForm(forms.Form):
    """Form that outputs the correct widgets for the information fields"""
    def __init__(self, *args, **kwargs):
        self.information_fields = kwargs.pop('fields')
        super(FieldsForm, self).__init__(*args, **kwargs)

        for key, field in self.information_fields.items():
            field_type = field["type"]

            if field_type == RegistrationInformationField.BOOLEAN_FIELD:
                self.fields[key] = forms.BooleanField(
                    required=False
                )
            elif field_type == RegistrationInformationField.INTEGER_FIELD:
                self.fields[key] = forms.IntegerField(
                    required=field["required"]
                )
            elif field_type == RegistrationInformationField.TEXT_FIELD:
                self.fields[key] = forms.CharField(
                    required=field["required"]
                )

            self.fields[key].label = field["label"]
            self.fields[key].help_text = field["description"]
            self.fields[key].initial = field['value']

    def field_values(self):
        for key, field in self.information_fields.items():
            yield (key, self.cleaned_data[key])
