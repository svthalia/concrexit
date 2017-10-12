from django import forms
from django.contrib.auth.models import User

from activemembers.models import CommitteeMembership


class CommitteeMembershipForm(forms.ModelForm):
    member = forms.ModelChoiceField(
        queryset=User.objects.order_by('first_name',
                                       'last_name'))

    class Meta:
        model = CommitteeMembership
        exclude = ()
