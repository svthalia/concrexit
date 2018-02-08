import os

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from sendfile import sendfile

from documents.models import (AnnualDocument, AssociationDocument,
                              GeneralMeeting, Document)
from utils.snippets import datetime_to_lectureyear


def index(request):
    lectureyear = datetime_to_lectureyear(timezone.now())

    years = {x: {} for x in range(1990, lectureyear + 1)}
    for policy in AnnualDocument.objects.filter(subcategory='policy'):
        years[policy.year]['policy'] = policy
    for report in AnnualDocument.objects.filter(subcategory='report'):
        years[report.year]['report']['annual'] = report
    for financial in AnnualDocument.objects.filter(subcategory='financial'):
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
    document = get_object_or_404(Document, pk=int(pk))

    if document.members_only and not request.user.is_authenticated:
        return redirect('/login/?next=%s' % request.path)

    try:
        file = document.file
    except ValueError:
        raise Http404('This document does not exist.')

    ext = os.path.splitext(file.path)[1]

    return sendfile(request, document.file.path, attachment=True,
                    attachment_filename=slugify(document.name) + ext)
