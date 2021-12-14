from django import forms

from activemembers.models import MemberGroup, MemberGroupMembership
from promotion.models import PromotionChannel

class RequestAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(RequestAdminForm, self).__init__(*args, **kwargs)
        paparazcie_object = MemberGroup.objects.filter(name = "Paparazcie")
        paparazcie_memberships = MemberGroupMembership.objects.filter(group_id = paparazcie_object.values().first()["id"])
        assigned_to_choices = [("", "---------")]
        for membership in paparazcie_memberships:
            assigned_to_choices.append(
                (
                    membership.member.id,
                    membership.member.get_full_name()
                )
            )
        self.fields["assigned_to"].choices = assigned_to_choices

        all_channels = PromotionChannel.objects.all()
        channel_choices = [("", "---------")]
        for x in all_channels:
            channel_choices.append(
                (
                    x.id,
                    x.name
                )
            )
        self.fields["channel"].choices = channel_choices
        