from django.contrib import admin
from django.forms import ModelForm

from activemembers.forms import CommitteeMembershipForm
from members.models import Member
from utils.translation import TranslatedModelAdmin
from . import models


class CommitteeMembershipInlineForm(ModelForm):
    """
    Form for the Committee Membership inline

    Doesn't do anything fancy, but we need it for speed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the related fields in advance
        self.fields['member'].queryset = Member.objects.select_related('user')


class CommitteeMembershipInline(admin.StackedInline):
    model = models.CommitteeMembership
    form = CommitteeMembershipInlineForm
    can_delete = False
    ordering = ('since',)
    extra = 0


@admin.register(models.Committee)
class CommitteeAdmin(TranslatedModelAdmin):
    inlines = (CommitteeMembershipInline,)
    list_display = ('name', 'since', 'until', 'active', 'email')
    list_filter = ('until', 'active',)
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)

    fields = ('name', 'description', 'photo', 'permissions', 'since',
              'until', 'contact_mailinglist', 'contact_email',
              'wiki_namespace', 'active')

    def email(self, instance):
        if instance.contact_email:
            return instance.contact_email
        elif instance.contact_mailinglist:
            return instance.contact_mailinglist.name + '@thalia.nu'
        return None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(board__is_board=True)


@admin.register(models.Board)
class BoardAdmin(TranslatedModelAdmin):
    inlines = (CommitteeMembershipInline,)
    exclude = ('is_board',)
    filter_horizontal = ('permissions',)

    fields = ('name', 'description', 'photo', 'permissions',
              'contact_mailinglist', 'contact_email', 'since', 'until',)


@admin.register(models.CommitteeMembership)
class CommitteeMembershipAdmin(TranslatedModelAdmin):
    form = CommitteeMembershipForm
    list_display = ('member', 'committee', 'since', 'until', 'chair', 'role')
    list_filter = ('committee',)
    search_fields = ('member__user__first_name', 'member__user__last_name',
                     'member__user__email')


@admin.register(models.Mentorship)
class MentorsAdmin(admin.ModelAdmin):
    pass
