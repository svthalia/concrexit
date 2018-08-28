"""Views provided by the documents package"""
import os

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from sendfile import sendfile

from documents.models import (AnnualDocument, AssociationDocument,
                              GeneralMeeting, Document)
from utils.snippets import datetime_to_lectureyear


def index(request):
    """
    View that renders the documents index page

    :param request: the request object
    :return: HttpResponse 200 containing the page HTML
    """
    lectureyear = datetime_to_lectureyear(timezone.now())

    years = {x: {} for x in range(1990, lectureyear + 1)}
    for policy in AnnualDocument.objects.filter(subcategory='policy'):
        years[policy.year]['policy'] = policy
    for report in AnnualDocument.objects.filter(subcategory='report'):
        if 'report' not in years[report.year]:
            years[report.year]['report'] = {}
        years[report.year]['report']['annual'] = report
    for financial in AnnualDocument.objects.filter(subcategory='financial'):
        if 'report' not in years[financial.year]:
            years[financial.year]['report'] = {}
        years[financial.year]['report']['financial'] = financial

    meeting_years = {x: [] for x in range(1990, lectureyear + 1)}
    for obj in GeneralMeeting.objects.all():
        meeting_year = datetime_to_lectureyear(obj.datetime)
        if meeting_year not in meeting_years:
            meeting_years[meeting_year] = []
        meeting_years[meeting_year].append(obj)

    return render(request, 'documents/index.html', {
        'association_documents': AssociationDocument.objects.all(),
        'annual_reports': sorted(years.items(), reverse=True),
        # TODO ideally we want to do this dynamically in CSS
        'annual_docs_width': (220 + 20) * len(years),
        'meeting_years': sorted(meeting_years.items(), reverse=True)
    })


# TODO verify if we need to check a permission instead.
# This depends on how we're dealing with ex-members.
def get_document(request, pk):
    """
    View that allows you to download a specific document based on it's and your
    permissions settings

    :param request: the request object
    :param pk: primary key of the document
    :return: either a 302 redirect to the login page or a 200 with the document
    """
    document = get_object_or_404(Document, pk=int(pk))

    if document.members_only and not request.user.is_authenticated:
        return redirect('{}?next={}'.format(settings.LOGIN_URL, request.path))

    lang = request.GET.get('language')
    try:
        if lang == 'nl':
            file = document.file_nl
        elif lang == 'en':
            file = document.file_en
        else:  # Fall back on language detection
            file = document.file
    except ValueError:
        raise Http404('This document does not exist.')

    ext = os.path.splitext(file.path)[1]

    return sendfile(request, file.path, attachment=True,
                    attachment_filename=slugify(document.name) + ext)
