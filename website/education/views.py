"""Views provided by the education package."""
import os
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from members.decorators import membership_required
from utils.media.services import get_media_url

from . import emails
from .forms import AddExamForm, AddSummaryForm
from .models import Category, Course, Exam, Summary


class CourseIndexView(ListView):
    """Render an overview of the courses."""

    queryset = Course.objects.filter(until=None).prefetch_related(
        "categories", "old_courses"
    )
    template_name = "education/courses.html"

    def get_ordering(self) -> str:
        return "name"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "courses": [
                    {
                        "course_code": x.course_code,
                        "name": x.name,
                        "categories": x.categories.all(),
                        "document_count": sum(
                            [
                                x.summary_set.filter(accepted=True).count(),
                                x.exam_set.filter(accepted=True).count(),
                            ]
                            + [
                                c.summary_set.filter(accepted=True).count()
                                + c.exam_set.filter(accepted=True).count()
                                for c in x.old_courses.all()
                            ]
                        ),
                        "url": x.get_absolute_url(),
                    }
                    for x in context["object_list"]
                ],
                "categories": Category.objects.all(),
            }
        )
        return context


class CourseDetailView(DetailView):
    """Render the detail page of one specific course."""

    model = Course
    context_object_name = "course"
    template_name = "education/course.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        obj = context["course"]
        courses = list(obj.old_courses.all())
        courses.append(obj)
        items = {}
        for course in courses:
            for summary in course.summary_set.filter(accepted=True):
                if summary.year not in items:
                    items[summary.year] = {
                        "summaries": [],
                        "exams": [],
                        "legacy": course if course.pk != obj.pk else None,
                    }
                items[summary.year]["summaries"].append(
                    {
                        "year": summary.year,
                        "name": summary.name,
                        "language": summary.language,
                        "id": summary.id,
                    }
                )
            for exam in course.exam_set.filter(accepted=True):
                if exam.year not in items:
                    items[exam.year] = {
                        "summaries": [],
                        "exams": [],
                        "legacy": course if course.pk != obj.pk else None,
                    }
                items[exam.year]["exams"].append(
                    {
                        "type": "exam",
                        "year": exam.year,
                        "name": f"{exam.get_type_display()} {exam.name}",
                        "language": exam.language,
                        "id": exam.id,
                    }
                )
        context.update({"items": sorted(items.items(), key=lambda x: x[0])})
        return context


@method_decorator(login_required, "dispatch")
@method_decorator(membership_required, "dispatch")
class ExamDetailView(DetailView):
    """Fetch and output the specified exam."""

    model = Exam

    def get(self, request, *args, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        obj = response.context_data["object"]
        obj.download_count += 1
        obj.save()

        ext = os.path.splitext(obj.file.name)[1]
        filename = f"{obj.course.name}-summary{obj.year}{ext}"
        return redirect(get_media_url(obj.file, attachment=filename))


@method_decorator(login_required, "dispatch")
@method_decorator(membership_required, "dispatch")
class SummaryDetailView(DetailView):
    """Fetch and output the specified summary."""

    model = Summary

    def get(self, request, *args, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        obj = response.context_data["object"]
        obj.download_count += 1
        obj.save()

        ext = os.path.splitext(obj.file.name)[1]
        filename = f"{obj.course.name}-summary{obj.year}{ext}"
        return redirect(get_media_url(obj.file, attachment=filename))


@method_decorator(login_required, "dispatch")
@method_decorator(membership_required, "dispatch")
class ExamCreateView(SuccessMessageMixin, CreateView):
    """Render the form to submit a new exam."""

    model = Exam
    form_class = AddExamForm
    template_name = "education/add_exam.html"
    success_url = reverse_lazy("education:submit-exam")
    success_message = _("Exam submitted successfully.")

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial["exam_date"] = date.today()
        initial["course"] = self.kwargs.get("pk", None)
        return initial

    def form_valid(self, form) -> HttpResponse:
        self.object = form.save(commit=False)
        self.object.uploader = self.request.member
        self.object.uploader_date = datetime.now()
        self.object.save()
        emails.send_document_notification(self.object)
        return super().form_valid(form)


@method_decorator(login_required, "dispatch")
@method_decorator(membership_required, "dispatch")
class SummaryCreateView(SuccessMessageMixin, CreateView):
    """Render the form to submit a new summary."""

    model = Summary
    form_class = AddSummaryForm
    template_name = "education/add_summary.html"
    success_url = reverse_lazy("education:submit-summary")
    success_message = _("Summary submitted successfully.")

    def get_initial(self):
        initial = super().get_initial()
        initial["author"] = self.request.member.get_full_name()
        initial["course"] = self.kwargs.get("pk", None)
        return initial

    def form_valid(self, form) -> HttpResponse:
        self.object = form.save(commit=False)
        self.object.uploader = self.request.member
        self.object.uploader_date = datetime.now()
        self.object.save()
        emails.send_document_notification(self.object)
        return super().form_valid(form)


@method_decorator(login_required, "dispatch")
class BookInfoView(TemplateView):
    """Render a page with information about book sale.

    Only available to members and to-be members
    """

    template_name = "education/books.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if request.member.has_active_membership() or (
            request.member.earliest_membership
            and request.member.earliest_membership.since > timezone.now().date()
        ):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
