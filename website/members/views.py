import json
import os
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from sendfile import sendfile

from . import models
from .forms import MemberForm


@login_required
def index(request):
    query_filter = '' if request.GET.get(
        'filter') is None else request.GET.get('filter')
    keywords = '' if request.GET.get('keywords') is None else request.GET.get(
        'keywords')

    page = request.GET.get('page')
    page = 1 if page is None or not page.isdigit() else int(page)

    start_year = date.today().year - 4
    # If language is English show one year less
    # since the width is smaller than needed for the translations to fit
    if request.LANGUAGE_CODE == 'en':
        start_year += 1
    year_range = reversed(range(start_year, date.today().year + 1))

    memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
    members_query = ~Q(id=None)

    if query_filter and query_filter.isdigit() and not (
                        query_filter == 'ex' or
                        query_filter == 'honor' or
                        query_filter == 'old'):
        members_query &= Q(starting_year=int(query_filter))
    elif query_filter == 'old':
        members_query &= Q(starting_year__lt=start_year)
    elif query_filter == 'ex':
        memberships = models.Membership.objects.filter(memberships_query)
        members_query &= ~Q(user__in=memberships.values('user'))
        memberships_query = Q(type='member') & Q(until__lte=datetime.now())
    elif query_filter == 'honor':
        memberships_query = Q(until__gt=datetime.now().date()) | Q(until=None)
        memberships_query &= Q(type='honorary')

    if keywords is not None:
        memberships_query &= (Q(user__member__nickname__icontains=keywords) |
                              Q(user__first_name__icontains=keywords) |
                              Q(user__last_name__icontains=keywords) |
                              Q(user__username__icontains=keywords))

    memberships = models.Membership.objects.filter(memberships_query)
    members_query &= Q(user__in=memberships.values('user'))
    members = models.Member.objects.filter(members_query).order_by(
            '-starting_year', 'user__first_name')

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
        member = get_object_or_404(models.Member, user=request.user)

    # Group the memberships under the committees for easier template rendering
    memberships = member.committeemembership_set.all()
    achievements = {}
    for membership in memberships:
        period = {
            'since': membership.since,
            'until': membership.until,
            'chair': membership.chair
        }

        if hasattr(membership.committee, 'board'):
            period['role'] = membership.role

        if (membership.until is None and
                hasattr(membership.committee, 'board')):
            period['until'] = membership.committee.board.until

        name = membership.committee.name
        if achievements.get(name):
            achievements[name]['periods'].append(period)
            if achievements[name]['earliest'] > membership.since:
                achievements[name]['earliest'] = membership.since
            achievements[name]['periods'].sort(key=lambda x: x['since'])
        else:
            achievements[name] = {
                'name': name,
                'periods': [period],
                'earliest': membership.since,
            }
    mentor_years = member.mentorship_set.all()
    for mentor_year in mentor_years:
        name = "Mentor in {}".format(mentor_year.year)
        # Ensure mentorships appear last but are sorted
        earliest = date.today()
        earliest = earliest.replace(year=earliest.year + mentor_year.year)
        if not achievements.get(name):
            achievements[name] = {
                'name': name,
                'earliest': earliest,
            }
    achievements = sorted(achievements.values(), key=lambda x: x['earliest'])
    return render(request, 'members/profile.html',
                  {'member': member, 'achievements': achievements})


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
