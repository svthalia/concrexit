import csv
import json
from datetime import date, datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django.views.generic.base import TemplateResponseMixin, View
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

import pizzas.services
from members import services, emails
from members.models import EmailChange, Membership
from . import models
from .forms import ProfileForm, EmailChangeForm
from .services import member_achievements


class ObtainThaliaAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data={
            'username': request.data.get('username').lower()
            if 'username' in request.data else None,
            'password': request.data.get('password')
        }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


def filter_users(tab, keywords, year_range):
    memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
    members_query = ~Q(id=None)

    if tab and tab.isdigit():
        members_query &= Q(profile__starting_year=int(tab))
    elif tab == 'old':
        members_query &= Q(profile__starting_year__lt=year_range[-1])
    elif tab == 'ex':
        # Filter out all current active memberships
        memberships_query &= Q(type='member') | Q(type='honorary')
        memberships = models.Membership.objects.filter(memberships_query)
        members_query &= ~Q(pk__in=memberships.values('user__pk'))
        # Members_query contains users that are not currently (honorary)member
    elif tab == 'honor':
        memberships_query = Q(until__gt=datetime.now().date()) | Q(until=None)
        memberships_query &= Q(type='honorary')

    if keywords:
        for key in keywords:
            members_query &= (
                (Q(profile__nickname__icontains=key) &
                 # Works because relevant options all have `nick` in their key
                 Q(profile__display_name_preference__contains='nick')) |
                Q(first_name__icontains=key) |
                Q(last_name__icontains=key) |
                Q(username__icontains=key))

    if tab == 'ex':
        memberships_query = Q(type='member') | Q(type='honorary')
        memberships = models.Membership.objects.filter(memberships_query)
        all_memberships = models.Membership.objects.all()
        # Only keep members that were once members, or are legacy users that
        #  do not have any memberships at all
        members_query &= (Q(pk__in=memberships.values('user__pk')) |
                          ~Q(pk__in=all_memberships.values('user__pk')))
    else:
        memberships = models.Membership.objects.filter(memberships_query)
        members_query &= Q(pk__in=memberships.values('user__pk'))
    return (models.Member.objects
            .filter(members_query)
            .order_by('-profile__starting_year',
                      'first_name'))


@login_required
def index(request):
    query_filter = '' if request.GET.get(
        'filter') is None else request.GET.get('filter')
    keywords = '' if request.GET.get('keywords') is None else request.GET.get(
        'keywords').split()

    page = request.GET.get('page')
    page = 1 if page is None or not page.isdigit() else int(page)

    start_year = date.today().year - 4
    # If language is English show one year less
    # since the width is smaller than needed for the translations to fit
    if request.LANGUAGE_CODE == 'en':
        start_year += 1
    year_range = list(reversed(range(start_year, date.today().year + 1)))

    members = filter_users(query_filter, keywords, year_range)

    paginator = Paginator(members, 24)

    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        members = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        members = paginator.page(paginator.num_pages)

    page_range = range(1, paginator.num_pages + 1)
    if paginator.num_pages > 7:
        if page > 3:
            page_range_end = paginator.num_pages
            if page + 3 <= paginator.num_pages:
                page_range_end = page + 3

            page_range = range(page - 2, page_range_end)
            while page_range.stop - page_range.start < 5:
                page_range = range(page_range.start - 1, page_range.stop)
        else:
            page_range = range(1, 6)

    return render(request, 'members/index.html',
                  {'members': members, 'filter': query_filter,
                   'year_range': year_range, 'page_range': page_range,
                   'keywords': keywords})


@login_required
def profile(request, pk=None):
    if pk:
        member = get_object_or_404(models.Member, pk=int(pk))
    else:
        member = request.member

    # Group the memberships under the committees for easier template rendering
    achievements = member_achievements(member)

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

    return render(request, 'members/profile.html',
                  {
                      'achievements': achievements,
                      'member': member,
                      'membership_type': membership_type,
                  })


@login_required
def account(request):
    return render(request, 'members/account.html')


@login_required
def edit_profile(request):
    profile = get_object_or_404(models.Profile, user=request.user)
    saved = False

    if request.POST:
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            saved = True
            form.save()
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'members/edit_profile.html',
                  {'form': form, 'saved': saved})


@permission_required('auth.change_user')
def iban_export(request):
    header_fields = ['name', 'username', 'iban']
    rows = []

    members = models.Member.current_members.filter(
        profile__direct_debit_authorized=True)

    for member in members:
        if member.current_membership.type != 'honorary':
            rows.append({
                'name': member.get_full_name(),
                'username': member.username,
                'iban': member.profile.bank_account
            })

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, header_fields)
    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    response['Content-Disposition'] = (
        'attachment; filename="iban-export.csv"')
    return response


@login_required
def statistics(request):
    member_types = (t[0] for t in Membership.MEMBERSHIP_TYPES)

    # The numbers
    total = models.Member.current_members.count()

    context = {
        "total_members": total,
        "total_stats_year": json.dumps(services.gen_stats_year(member_types)),
        "total_stats_member_type": json.dumps(
            services.gen_stats_member_type(member_types)),
        "total_pizza_orders": json.dumps(
            pizzas.services.gen_stats_pizza_orders()),
        "current_pizza_orders": json.dumps(
            pizzas.services.gen_stats_current_pizza_orders()),
    }

    return render(request, 'members/statistics.html', context)


@method_decorator(login_required, name='dispatch')
class EmailChangeFormView(FormView):
    """
    View that renders the email change form
    """
    form_class = EmailChangeForm
    template_name = 'members/email_change.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['email'] = self.request.member.email
        return initial

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST['member'] = request.member.pk
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        change_request = form.save()
        emails.send_email_change_confirmation_messages(change_request)
        return TemplateResponse(request=self.request,
                                template='members/email_change_requested.html')


@method_decorator(login_required, name='dispatch')
class EmailChangeConfirmView(View, TemplateResponseMixin):
    """
    View that renders an HTML template and confirms the old email address
    """
    template_name = 'members/email_change_confirmed.html'

    def get(self, request, *args, **kwargs):
        if not EmailChange.objects.filter(confirm_key=kwargs['key']).exists():
            raise Http404

        change_request = EmailChange.objects.get(confirm_key=kwargs['key'])

        services.confirm_email_change(change_request)

        return self.render_to_response({})


@method_decorator(login_required, name='dispatch')
class EmailChangeVerifyView(View, TemplateResponseMixin):
    """
    View that renders an HTML template and verifies the new email address
    """
    template_name = 'members/email_change_verified.html'

    def get(self, request, *args, **kwargs):
        if not EmailChange.objects.filter(verify_key=kwargs['key']).exists():
            raise Http404

        change_request = EmailChange.objects.get(verify_key=kwargs['key'])

        services.verify_email_change(change_request)

        return self.render_to_response({})
