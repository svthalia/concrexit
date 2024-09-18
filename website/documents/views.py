"""Views provided by the documents package."""
import os
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import DetailView, TemplateView

from documents.models import (
    AnnualDocument,
    AssociationDocument,
    Document,
    GeneralMeeting,
)
from utils.media.services import get_media_url
from utils.snippets import datetime_to_lectureyear


class DocumentsIndexView(TemplateView):
    """View that renders the documents index page."""

    template_name = "documents/index.html"

    def get_context_data(self, **kwargs) -> dict:
        lecture_year = datetime_to_lectureyear(timezone.now())

        years = defaultdict(
            lambda: {
                "documents": {"policy": None, "report": None, "financial": None},
                "general_meetings": [],
            }
        )

        # Ensure that all years up to now are in the dict, even if there are no documents.
        # Using a defaultdict means that future years will be added automatically iff a
        # document exists for that year, such as a policy plan for the upcoming year.
        for year in range(1990, lecture_year + 1):
            years[year] = years[year]

        for document in AnnualDocument.objects.filter(
            subcategory__in=("policy", "report", "financial")
        ):
            years[document.year]["documents"][document.subcategory] = document

        for obj in GeneralMeeting.objects.all():
            meeting_year = datetime_to_lectureyear(obj.datetime)
            years[meeting_year]["general_meetings"].append(obj)

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "association_documents": AssociationDocument.objects.order_by(
                    "name"
                ).all(),
                "years": sorted(years.items(), reverse=True),
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
            return redirect(reverse(settings.LOGIN_URL) + f"?next={request.path}")
        if document.members_only and not request.member.has_active_membership():
            raise PermissionDenied

        try:
            file = document.file
        except ValueError as e:
            raise Http404("This document does not exist.") from e

        ext = os.path.splitext(file.name)[1]

        return redirect(get_media_url(file, attachment=slugify(document.name) + ext))
