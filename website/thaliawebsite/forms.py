"""Special forms."""
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from django.utils.translation import gettext_lazy as _

from utils.snippets import send_email


class AuthenticationForm(BaseAuthenticationForm):
    """Override the authentication form provided by Django."""

    def clean(self):
        """Lowercase the username."""
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()


class EmailSenderForm(forms.Form):
    recipients = forms.CharField(
        label=_("Recipients"),
        help_text=_("Enter multiple email addresses separated by commas."),
        required=True,
    )
    cc_recipients = forms.CharField(
        label=_("CC recipients (optional)"),
        help_text=_("Enter multiple email addresses separated by commas."),
        required=False,
    )
    bcc_recipients = forms.CharField(
        label=_("BCC recipients (optional)"),
        help_text=_(
            "Enter multiple email addresses separated by commas. Emails will always be sent to %s as well."
        )
        % settings.DEFAULT_FROM_EMAIL,
        required=False,
    )

    reply_to = forms.CharField(
        label=_("Reply to-addresses (optional)"),
        help_text=_(
            "Enter multiple email addresses separated by commas. Will be set as reply-to email address. "
            "Emails will always be sent from %s."
        )
        % settings.DEFAULT_FROM_EMAIL,
        required=False,
    )

    subject = forms.CharField(label=_("Subject"))
    message = forms.CharField(
        label=_("Message body"),
        help_text=_("Supports or simple HTML (but be careful with that)."),
        widget=forms.Textarea,
    )

    def clean_recipients(self):
        return self.email_address_cleaner("recipients")

    def clean_bcc_recipients(self):
        return self.email_address_cleaner("bcc_recipients")

    def clean_cc_recipients(self):
        return self.email_address_cleaner("cc_recipients")

    def clean_reply_to(self):
        return self.email_address_cleaner("reply_to")

    def email_address_cleaner(self, field_name):
        recipients = self.cleaned_data[field_name].split(",")
        recipients = [r.strip() for r in recipients]

        if recipients == [""]:
            return None

        # validate that all recipients are valid email addresses
        for recipient in recipients:
            if not forms.EmailField().clean(recipient):
                raise forms.ValidationError(
                    _("Invalid email address: %(email)s"), params={"email": recipient}
                )

        return recipients

    def send(self):
        txt_template = "email/email_sender_email.txt"
        html_template = "email/email_sender_email.html"

        bcc = self.cleaned_data["bcc_recipients"] or []
        bcc += settings.DEFAULT_FROM_EMAIL

        send_email(
            to=self.cleaned_data["recipients"],
            subject=self.cleaned_data["subject"],
            txt_template=txt_template,
            context={"message": self.cleaned_data["message"]},
            html_template=html_template,
            bcc=bcc,
            cc=self.cleaned_data["cc_recipients"],
            reply_to=self.cleaned_data["reply_to"],
        )
