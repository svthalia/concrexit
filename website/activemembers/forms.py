"""The forms defined by the activemembers module."""
from django import forms
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _

from activemembers.models import MemberGroupMembership
from members.models import Member


class MemberGroupMembershipForm(forms.ModelForm):
    """Custom form for group memberships that orders the members."""

    member = forms.ModelChoiceField(
        queryset=Member.objects.order_by("first_name", "last_name"),
        label=_("Member"),
    )

    class Meta:
        model = MemberGroupMembership
        fields = "__all__"


class MemberGroupForm(forms.ModelForm):
    """Solely here for performance reasons.

    Needed because the `__str__()` of `Permission` (which is displayed in the
    permissions selection box) also prints the corresponding app and
    `content_type` for each permission.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = Permission.objects.select_related(
            "content_type"
        )
