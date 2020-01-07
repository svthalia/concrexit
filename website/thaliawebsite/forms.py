"""Special forms"""
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm


class AuthenticationForm(BaseAuthenticationForm):
    """Override the authentication form provided by Django"""

    def clean(self):
        """Lowercase the username"""
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()
