from django import forms
from django.utils.translation import gettext_lazy as _


class EventMessageForm(forms.Form):
    """Form that outputs a widget to get info to send a push notification."""

    title = forms.CharField(label=_("title"), max_length=150)
    body = forms.CharField(label=_("body"), widget=forms.Textarea)
    url = forms.CharField(
        max_length=256,
        required=False,
        help_text=_("The notification opens to the event by default."),
    )
