from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from documents.models import AssociationDocumentsYear, MiscellaneousDocument
from documents.models import GeneralMeeting, GeneralMeetingDocument
from utils.snippets import datetime_to_lectureyear

from sendfile import sendfile
import os


def index(request):
    years = {x: None for x in range(1990, timezone.now().year)}
    for obj in AssociationDocumentsYear.objects.all():
        years[obj.year] = {'policy': [obj.policy_document],
                           'report': [obj.annual_report, obj.financial_report],
                           }
    for year_docs in years.values():
        if year_docs is not None:
            for docs in year_docs.values():
                # Duplicate list to prevent disrupting iteration by removing
                for doc in list(docs):
                    try:
                        doc.file
                    except ValueError:
                        docs.remove(doc)

    meeting_years = {x: [] for x in range(1990, timezone.now().year)}
    for obj in GeneralMeeting.objects.all():
        meeting_years[datetime_to_lectureyear(obj.datetime)].append(obj)

    context = {'miscellaneous_documents': MiscellaneousDocument.objects.all(),
               'association_documents_years': sorted(years.items(),
                                                     reverse=True),
               # TODO ideally we want to do this dynamically in CSS
               'assocation_docs_width': (220 + 20) * len(years),
               'meeting_years': sorted(meeting_years.items(), reverse=True)
               }
    return render(request, 'documents/index.html', context)


def get_miscellaneous_document(request, pk):
    document = get_object_or_404(MiscellaneousDocument, pk=int(pk))
    # TODO verify if we need to check a permission instead.
    # This depends on how we're dealing with ex-members.
    if document.members_only and not request.user.is_authenticated():
        raise PermissionDenied
    return sendfile(request, document.file.path, attachment=True)


# TODO verify if we need to check a permission instead.
@login_required
def get_association_document(request, document_type, year):
    documents = get_object_or_404(AssociationDocumentsYear, year=int(year))
    file = {'policy-document': documents.policy_document,
            'annual-report': documents.annual_report,
            'financial-report': documents.financial_report}[document_type]
    _, ext = os.path.splitext(file.path)
    filename = '{}-{}-{}{}'.format(year, int(year)+1, document_type, ext)
    return sendfile(request, file.path,
                    attachment=True, attachment_filename=filename)


# TODO verify if we need to check a permission instead.
@login_required
def get_general_meeting_document(request, pk, document_pk):
    document = get_object_or_404(GeneralMeetingDocument, pk=int(document_pk))
    # TODO consider if we want to format the filename differently
    return sendfile(request, document.file.path, attachment=True)


# TODO verify if we need to check a permission instead.
@login_required
def get_general_meeting_minutes(request, pk):
    meeting = get_object_or_404(GeneralMeeting, pk=int(pk))
    _, ext = os.path.splitext(meeting.minutes.path)
    filename = '{}-minutes{}'.format(meeting.datetime.date(), ext)
    return sendfile(request, meeting.minutes.path,
                    attachment=True, attachment_filename=filename)
