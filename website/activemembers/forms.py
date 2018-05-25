"""The forms defined by the activemembers module"""
from django import forms

from activemembers.models import CommitteeMembership
from members.models import Member


class CommitteeMembershipForm(forms.ModelForm):
    """Custom form for committee memberships that orders the members"""
    member = forms.ModelChoiceField(
        queryset=Member.objects.order_by('first_name',
                                         'last_name'))

    class Meta:
        model = CommitteeMembership
        exclude = ()
