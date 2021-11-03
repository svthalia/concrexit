"""Views provided by the documents package."""
import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView, DetailView
from django_sendfile import sendfile

from documents.models import (
    AnnualDocument,
    AssociationDocument,
    GeneralMeeting,
    Document,
)
from utils.snippets import datetime_to_lectureyear


class DocumentsIndexView(TemplateView):
    """View that renders the documents index page."""

    template_name = "documents/index.html"

    def get_context_data(self, **kwargs) -> dict:
        lecture_year = datetime_to_lectureyear(timezone.now())

        years = {x: {} for x in reversed(range(1990, lecture_year + 1))}
        for year in years:
            years[year] = {
                "documents": {"policy": None, "report": None, "financial": None},
                "general_meetings": [],
            }

        for document in AnnualDocument.objects.filter(subcategory="policy"):
            years[document.year]["documents"]["policy"] = document
        for document in AnnualDocument.objects.filter(subcategory="report"):
            years[document.year]["documents"]["report"] = document
        for document in AnnualDocument.objects.filter(subcategory="financial"):
            years[document.year]["documents"]["financial"] = document

        for obj in GeneralMeeting.objects.all():
            meeting_year = datetime_to_lectureyear(obj.datetime)
            years[meeting_year]["general_meetings"].append(obj)

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "association_documents": AssociationDocument.objects.order_by(
                    "name"
                ).all(),
                "years": list(years.items()),
            }
        )
        return context


class DocumentDownloadView(DetailView):
    """View that allows you to download a specific document based on it's and your permissions settings."""

    model = Document

    def get(self, request, *args, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        document = response.context_data["document"]

        if document.members_only and not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if document.members_only and not request.member.has_active_membership():
            raise PermissionDenied

        try:
            file = document.file
        except ValueError as e:
            raise Http404("This document does not exist.") from e

        ext = os.path.splitext(file.path)[1]

        return sendfile(
            request,
            file.path,
            attachment=True,
            attachment_filename=slugify(document.name) + ext,
        )
