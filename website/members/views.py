"""Views provided by the members package."""
import json
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.base import TemplateResponseMixin, TemplateView, View

import activemembers.services as activemembers_services
import events.services as event_services
import pizzas.services
from members import emails, services
from members.decorators import membership_required
from members.models import EmailChange, Member, Membership, Profile
from thaliawebsite.views import PagedView
from utils.media.services import fetch_thumbnails
from utils.snippets import datetime_to_lectureyear

from . import models
from .forms import ProfileForm
from .services import member_achievements, member_societies


@method_decorator(login_required, "dispatch")
@method_decorator(membership_required, "dispatch")
class MembersIndex(PagedView):
    """View that renders the members overview."""

    model = Member
    paginate_by = 28
    template_name = "members/index.html"
    context_object_name = "members"
    keywords = None
    query_filter = ""
    year_range = []

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)
        current_lectureyear = datetime_to_lectureyear(date.today())
        self.year_range = list(
            reversed(range(current_lectureyear - 5, current_lectureyear + 1))
        )
        self.keywords = request.GET.get("keywords", "").split() or None
        self.query_filter = kwargs.get("filter", None)

    def get_queryset(self) -> QuerySet:
        memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
        members_query = ~Q(id=None)

        if self.query_filter and self.query_filter.isdigit():
            members_query &= Q(profile__starting_year=int(self.query_filter))
            memberships_query &= Q(type=Membership.MEMBER)
        elif self.query_filter == "older":
            members_query &= Q(profile__starting_year__lt=self.year_range[-1])
            memberships_query &= Q(type=Membership.MEMBER)
        elif self.query_filter == "former":
            # Filter out all current active memberships
            memberships_query &= Q(type=Membership.MEMBER) | Q(type=Membership.HONORARY)
            memberships = Membership.objects.filter(memberships_query)
            members_query &= ~Q(pk__in=memberships.values("user__pk"))
        # Members_query contains users that are not currently (honorary)member
        elif self.query_filter == "benefactors":
            memberships_query &= Q(type=Membership.BENEFACTOR)
        elif self.query_filter == "honorary":
            memberships_query = Q(until__gt=datetime.now().date()) | Q(until=None)
            memberships_query &= Q(type=Membership.HONORARY)

        if self.keywords:
            for key in self.keywords:
                # Works because relevant options all have `nick` in their key
                members_query &= (
                    (
                        Q(profile__nickname__icontains=key)
                        & Q(profile__display_name_preference__contains="nick")
                    )
                    | Q(first_name__icontains=key)
                    | Q(last_name__icontains=key)
                    | Q(username__icontains=key)
                )

        if self.query_filter == "former":
            memberships_query = Q(type=Membership.MEMBER) | Q(type=Membership.HONORARY)
            memberships = Membership.objects.filter(memberships_query)
            all_memberships = Membership.objects.all()
            # Only keep members that were once members, or are legacy users
            # that do not have any memberships at all
            members_query &= Q(pk__in=memberships.values("user__pk")) | ~Q(
                pk__in=all_memberships.values("user__pk")
            )
        else:
            memberships = Membership.objects.filter(memberships_query)
            members_query &= Q(pk__in=memberships.values("user__pk"))
        members = (
            Member.objects.filter(members_query)
            .order_by("first_name")
            .select_related("profile")
        )
        return members

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "filter": self.query_filter,
                "year_range": self.year_range,
                "keywords": self.keywords,
            }
        )

        fetch_thumbnails(
            [x.profile.photo for x in context["object_list"] if x.profile.photo]
        )

        return context


@method_decorator(login_required, "dispatch")
class ProfileDetailView(DetailView):
    """View that renders a member's profile."""

    context_object_name = "member"
    model = Member
    template_name = "members/user/profile.html"

    def setup(self, request, *args, **kwargs) -> None:
        if "pk" not in kwargs and request.member:
            kwargs["pk"] = request.member.pk
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        member = context["member"]

        achievements = member_achievements(member)
        societies = member_societies(member)

        membership = member.current_membership
        membership_type = _("Unknown membership history")
        if membership:
            membership_type = membership.get_type_display()
        elif member.has_been_honorary_member():
            membership_type = _("Former honorary member")
        elif member.has_been_member():
            membership_type = _("Former member")
        elif member.latest_membership:
            membership_type = _("Former benefactor")

        context.update(
            {
                "achievements": achievements,
                "societies": societies,
                "membership_type": membership_type,
            }
        )

        return context


@method_decorator(login_required, "dispatch")
class UserProfileUpdateView(SuccessMessageMixin, UpdateView):
    """View that allows a user to update their profile."""

    template_name = "members/user/edit_profile.html"
    model = Profile
    form_class = ProfileForm
    success_url = reverse_lazy("members:edit-profile")
    success_message = _("Your profile has been updated successfully.")

    def get_object(self, queryset=None) -> Profile:
        return get_object_or_404(models.Profile, user=self.request.user)


@method_decorator(login_required, "dispatch")
class StatisticsView(TemplateView):
    """View that renders the statistics page."""

    template_name = "members/statistics.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_members": models.Member.current_members.count(),
                "cohort_sizes": json.dumps(services.gen_stats_year()),
                "member_type_distribution": json.dumps(
                    services.gen_stats_member_type()
                ),
                "committee_sizes": json.dumps(
                    activemembers_services.generate_statistics()
                ),
                "event_categories": json.dumps(
                    event_services.generate_category_statistics()
                ),
                "total_pizza_orders": json.dumps(
                    pizzas.services.gen_stats_pizza_orders()
                ),
                "active_members": json.dumps(services.gen_stats_active_members()),
            }
        )

        return context


@method_decorator(login_required, name="dispatch")
class EmailChangeFormView(CreateView):
    """View that renders the email change form."""

    model = EmailChange
    fields = ["email", "member"]
    template_name = "members/user/email_change.html"

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial["email"] = self.request.member.email
        return initial

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST["member"] = request.member.pk
        return super().post(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        change_request = form.save()
        emails.send_email_change_confirmation_messages(change_request)
        return TemplateResponse(
            request=self.request, template="members/user/email_change_requested.html"
        )


@method_decorator(login_required, name="dispatch")
class EmailChangeConfirmView(View, TemplateResponseMixin):
    """View that renders an HTML template and confirms the old email address."""

    template_name = "members/user/email_change_confirmed.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if not EmailChange.objects.filter(confirm_key=kwargs["key"]).exists():
            raise Http404

        change_request = EmailChange.objects.get(confirm_key=kwargs["key"])

        services.confirm_email_change(change_request)

        return self.render_to_response({})


@method_decorator(login_required, name="dispatch")
class EmailChangeVerifyView(View, TemplateResponseMixin):
    """View that renders an HTML template and verifies the new email address."""

    template_name = "members/user/email_change_verified.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if not EmailChange.objects.filter(verify_key=kwargs["key"]).exists():
            raise Http404

        change_request = EmailChange.objects.get(verify_key=kwargs["key"])

        services.verify_email_change(change_request)

        return self.render_to_response({})
