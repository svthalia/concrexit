from django.contrib import admin
from django.contrib.auth.models import Permission
from django.forms import BaseInlineFormSet, ModelForm

from activemembers.forms import CommitteeMembershipForm
from utils.translation import TranslatedModelAdmin
from . import models


class CommitteeMembershipInlineFormSet(BaseInlineFormSet):
    """
    Solely here for performance reasons.

    Needed because the `__str__()` of `CommitteeMembership` (which is displayed
    above each inline form) uses the username, name of the member and name of
    the committee.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.select_related('member', 'committee')


class CommitteeMembershipInline(admin.StackedInline):
    model = models.CommitteeMembership
    formset = CommitteeMembershipInlineFormSet
    can_delete = False
    ordering = ('since',)
    extra = 0
    # TODO: replace this with `autocomplete_fields` in Django 2.0
    raw_id_fields = ('member',)


class CommitteeForm(ModelForm):
    """
    Solely here for performance reasons.

    Needed because the `__str__()` of `Permission` (which is displayed in the
    permissions selection box) also prints the corresponding app and
    `content_type` for each permission.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = (Permission
                                               .objects
                                               .select_related('content_type'))


@admin.register(models.Committee)
class CommitteeAdmin(TranslatedModelAdmin):
    inlines = (CommitteeMembershipInline,)
    form = CommitteeForm
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
    form = CommitteeForm
    exclude = ('is_board',)
    filter_horizontal = ('permissions',)

    fields = ('name', 'description', 'photo', 'permissions',
              'contact_mailinglist', 'contact_email', 'since', 'until',)


@admin.register(models.CommitteeMembership)
class CommitteeMembershipAdmin(TranslatedModelAdmin):
    form = CommitteeMembershipForm
    list_display = ('member', 'committee', 'since', 'until', 'chair', 'role')
    list_filter = ('committee',)
    list_select_related = ('member', 'committee',)
    search_fields = ('member__first_name', 'member__last_name',
                     'member__email')


@admin.register(models.Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_select_related = ('member',)
