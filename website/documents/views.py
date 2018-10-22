"""Views provided by the documents package"""
import os

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import get_language
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

    years = {x: {} for x in reversed(range(1990, lectureyear + 1))}
    for year in years:
        years[year] = {
            'documents': {
                'policy': None,
                'report': None,
                'financial': None
            },
            'general_meetings': []
        }

    for document in AnnualDocument.objects.filter(subcategory='policy'):
        years[document.year]['documents']['policy'] = document
    for document in AnnualDocument.objects.filter(subcategory='report'):
        years[document.year]['documents']['report'] = document
    for document in AnnualDocument.objects.filter(subcategory='financial'):
        years[document.year]['documents']['financial'] = document

    for obj in GeneralMeeting.objects.all():
        meeting_year = datetime_to_lectureyear(obj.datetime)
        years[meeting_year]['general_meetings'].append(obj)

    return render(request, 'documents/index.html', {
        'association_documents':
            AssociationDocument
            .objects
            .order_by(f'name_{ get_language() }')
            .all(),
        'years': list(years.items())
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
