import os
from datetime import date
from sendfile import sendfile

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify

from .models import BecomeAMemberDocument, Member
from .forms import MemberForm


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

    members = Member.objects.all()
    if query_filter and query_filter.isdigit() and not (
                        query_filter == 'ex' or
                        query_filter == 'honor' or
                        query_filter == 'old'):
        members = [obj for obj in members if
                   obj.current_membership and
                   obj.current_membership.since.year == int(query_filter)]
    elif query_filter == 'old':
        members = [obj for obj in members if
                   obj.current_membership and
                   obj.current_membership.since.year < start_year]
    elif query_filter == 'ex':
        members = [obj for obj in members if not obj.current_membership and
                   obj.membership_set.filter(type='member').count() > 0]
    elif query_filter == 'honor':
        members = [obj for obj in members if
                   obj.current_membership and
                   obj.current_membership.type == 'honorary']
    else:
        members = [obj for obj in members if obj.current_membership]

    if keywords:
        members = [obj for obj in members if
                   keywords in obj.nickname.lower() or
                   keywords in obj.user.first_name.lower() or
                   keywords in obj.user.last_name.lower() or
                   keywords in obj.user.username.lower()]

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
        member = get_object_or_404(Member, pk=int(pk))
    else:
        member = get_object_or_404(Member, user=request.user)

    # Group the memberships under the committees for easier template rendering
    memberships = member.committeemembership_set.all()
    achievements = {}
    for membership in memberships:
        name = membership.committee.name
        if achievements.get(name):
            achievements[name]['periods'].append({
                'since': membership.since,
                'until': membership.until,
                'chair': membership.chair
            })
        else:
            achievements[name] = {
                'name': name,
                'periods': [{
                    'since': membership.since,
                    'until': membership.until,
                    'chair': membership.chair
                }]
            }
        achievements[name]['periods'].sort(key=lambda period: period['since'])

    mentor_years = member.mentorship_set.all()
    for mentor_year in mentor_years:
        name = str(mentor_year)
        if not achievements.get(name):
            achievements[name] = {
                'name': name
            }

    return render(request, 'members/profile.html',
                  {'member': member, 'achievements': achievements.values()})


@login_required
def account(request):
    return render(request, 'members/account.html')


@login_required
def edit_profile(request):
    member = get_object_or_404(Member, user=request.user)
    saved = False

    if request.POST:
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            saved = True
            member = form.save()

    form = MemberForm(instance=member)

    return render(request, 'members/edit_profile.html',
                  {'form': form, 'saved': saved})


def become_a_member(request):
    context = {'documents': BecomeAMemberDocument.objects.all()}
    return render(request, 'singlepages/become_a_member.html', context)


def get_become_a_member_document(request, pk):
    document = get_object_or_404(BecomeAMemberDocument, pk=int(pk))
    ext = os.path.splitext(document.file.path)[1]
    return sendfile(request, document.file.path, attachment=True,
                    attachment_filename=slugify(document.name) + ext)


def statistics(request):
    member_types = ["member", "supporter", "honorary"]

    # The numbers
    total = Member.active_members.count()

    context = {
            "total_members": total,
            "total_stats_year": gen_stats_year(member_types),
            "total_stats_member_type": gen_stats_member_type(member_types)
    }

    return render(request, 'members/statistics.html', context)


def gen_stats_member_type(member_types):
    total = dict()
    for member_type in member_types:
        total[member_type] = (Member
                              .active_members
                              .filter(user__membership__type=member_type)
                              .count())
    return total


def gen_stats_year(member_types):
    """
    Generate list with 6 entries, where each entry represents the total amount
    of Thalia members in a year. The sixth element contains all the multi-year
    students.
    """
    stats_year = []
    current_year = date.today().year

    for i in range(5):
        new = dict()
        for member_type in member_types:
            new[member_type] = (Member
                                .active_members
                                .filter(starting_year=current_year - i)
                                .filter(user__membership__type=member_type)
                                .count())
        stats_year.append(new)

    # Add multi year members
    new = dict()
    for member_type in member_types:
        new[member_type] = (Member
                            .active_members
                            .filter(starting_year__lt=current_year - 4)
                            .filter(user__membership__type=member_type)
                            .count())
    stats_year.append(new)

    return stats_year
