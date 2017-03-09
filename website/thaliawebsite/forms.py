from django.contrib.auth.forms import (AuthenticationForm as
                                       BaseAuthenticationForm)


class AuthenticationForm(BaseAuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)

    def clean(self):
        if 'username' in self.cleaned_data:
            self.cleaned_data['username'] = (self.cleaned_data['username']
                                             .lower())
        super().clean()
