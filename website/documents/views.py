from django.shortcuts import render
from django.utils import timezone

from documents.models import AssociationDocumentsYear, GenericDocument


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

    context = {'generic_documents': GenericDocument.objects.all(),
               'association_documents_years': sorted(years.items(),
                                                     reverse=True),
               # TODO ideally we want to do this dynamically in CSS
               'assocation_docs_width': (220 + 20) * len(years),
               }
    return render(request, 'documents/index.html', context)
