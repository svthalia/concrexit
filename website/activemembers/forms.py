"""The forms defined by the activemembers module"""
from django import forms

from activemembers.models import MemberGroupMembership
from members.models import Member


class MemberGroupMembershipForm(forms.ModelForm):
    """Custom form for group memberships that orders the members"""
    member = forms.ModelChoiceField(
        queryset=Member.objects.order_by('first_name',
                                         'last_name'))

    class Meta:
        model = MemberGroupMembership
        exclude = ()
