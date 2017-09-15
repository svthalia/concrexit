import csv
import json
import os
from datetime import date, datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.utils.translation import gettext as _
from sendfile import sendfile

from members.models import Member
from members.services import member_achievements
from . import models
from .forms import MemberForm


def filter_users(tab, keywords, year_range):
    memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
    members_query = ~Q(id=None)

    if tab and tab.isdigit():
        members_query &= Q(starting_year=int(tab))
    elif tab == 'old':
        members_query &= Q(starting_year__lt=year_range[-1])
    elif tab == 'ex':
        # Filter out all current active memberships
        memberships_query &= Q(type='member') | Q(type='honorary')
        memberships = models.Membership.objects.filter(memberships_query)
        members_query &= ~Q(user__in=memberships.values('user'))
        # Members_query contains users that are not currently (honorary)member
    elif tab == 'honor':
        memberships_query = Q(until__gt=datetime.now().date()) | Q(until=None)
        memberships_query &= Q(type='honorary')

    if keywords:
        for key in keywords:
            members_query &= (
                (Q(user__member__nickname__icontains=key) &
                 # Works because relevant options all have `nick` in their key
                 Q(user__member__display_name_preference__contains='nick')) |
                Q(user__first_name__icontains=key) |
                Q(user__last_name__icontains=key) |
                Q(user__username__icontains=key))

    if tab == 'ex':
        memberships_query = Q(type='member') | Q(type='honorary')
        memberships = models.Membership.objects.filter(memberships_query)
        all_memberships = models.Membership.objects.all()
        # Only keep members that were once members, or are legacy users that
        #  do not have any memberships at all
        members_query &= (Q(user__in=memberships.values('user')) |
                          ~Q(user__in=all_memberships.values('user')))
    else:
        memberships = models.Membership.objects.filter(memberships_query)
        members_query &= Q(user__in=memberships.values('user'))
    return (models.Member.objects.filter(members_query)
                                 .order_by('-starting_year',
                                           'user__first_name'))


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
        member = get_object_or_404(models.Member, user__pk=int(pk))
    else:
        member = get_object_or_404(models.Member, user=request.user)

    # Group the memberships under the committees for easier template rendering
    achievements = member_achievements(member)

    membership = member.current_membership
    membership_type = _("Former member")
    if membership:
        membership_type = membership.get_type_display()
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
    member = get_object_or_404(models.Member, user=request.user)
    saved = False

    if request.POST:
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            saved = True
            form.save()
    else:
        form = MemberForm(instance=member)

    return render(request, 'members/edit_profile.html',
                  {'form': form, 'saved': saved})


@permission_required('auth.change_user')
def iban_export(request):
    header_fields = ['name', 'username', 'iban']
    rows = []

    members = Member.active_members.filter(direct_debit_authorized=True)

    for member in members:
        if (member.current_membership.type != 'honorary'):
            rows.append({
                'name': member.get_full_name(),
                'username': member.user.username,
                'iban': member.bank_account
            })

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, header_fields)
    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    response['Content-Disposition'] = (
        'attachment; filename="iban-export.csv"')
    return response


def become_a_member(request):
    context = {'documents': models.BecomeAMemberDocument.objects.all()}
    return render(request, 'singlepages/become_a_member.html', context)


def get_become_a_member_document(request, pk):
    document = get_object_or_404(models.BecomeAMemberDocument, pk=int(pk))
    ext = os.path.splitext(document.file.path)[1]
    return sendfile(request,
                    document.file.path,
                    attachment=True,
                    attachment_filename=slugify(document.name) + ext)


def statistics(request):
    member_types = ("member", "supporter", "honorary")

    # The numbers
    total = models.Member.active_members.count()

    context = {
        "total_members": total,
        "total_stats_year": json.dumps(models.gen_stats_year(member_types)),
        "total_stats_member_type": json.dumps(
            models.gen_stats_member_type(member_types)),
    }

    return render(request, 'members/statistics.html', context)
