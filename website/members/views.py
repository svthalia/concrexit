from datetime import date
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from . import models

import os
from sendfile import sendfile


def index(request):
    members = models.Member.objects.all()

    paginator = Paginator(members, 12)
    page = request.GET.get('page')
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        members = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        members = paginator.page(paginator.num_pages)

    query_filter = request.GET.get('filter')
    year_range = reversed(range(date.today().year - 4, date.today().year + 1))

    return render(request, 'members/index.html', {'members': members, 'filter': query_filter, 'year_range': year_range})


def detail(request, id):
    members = models.Member.objects.all()
    filter = request.GET.get('filter')
    year_range = reversed(range(date.today().year - 4, date.today().year + 1))

    return render(request, 'members/index.html', {'members': members, 'filter': filter, 'year_range': year_range})


def become_a_member(request):
    context = {'documents': models.BecomeAMemberDocument.objects.all()}
    return render(request, 'singlepages/become_a_member.html', context)


def get_become_a_member_document(request, pk):
    document = get_object_or_404(models.BecomeAMemberDocument, pk=int(pk))
    ext = os.path.splitext(document.file.path)[1]
    return sendfile(request, document.file.path, attachment=True,
                    attachment_filename=slugify(document.name) + ext)
