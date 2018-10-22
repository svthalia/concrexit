"""Views provided by the education package"""
import os
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, get_language
from sendfile import sendfile

from members.decorators import membership_required
from .forms import AddExamForm, AddSummaryForm
from .models import Category, Course, Exam, Summary


def courses(request):
    """
    Renders an overview of the courses

    :param request: the request object
    :return: HttpResponse 200 containing the HTML as body
    """
    categories = Category.objects.all()
    courses = [
        {
            'course_code': x.course_code,
            'name': x.name,
            'categories': x.categories.all(),
            'document_count': sum([x.summary_set.filter(accepted=True).count(),
                                   x.exam_set.filter(accepted=True).count()] +
                                  [c.summary_set.filter(accepted=True).count()
                                   + c.exam_set.filter(accepted=True).count()
                                   for c in
                                   x.old_courses.all()]),
            'url': x.get_absolute_url()
        } for x in
        Course.objects.order_by(f'name_{ get_language() }').filter(
            until=None)
    ]

    return render(request, 'education/courses.html',
                  {'courses': courses, 'categories': categories})


def course(request, id):
    """
    Renders the detail page of one specific course

    :param request: the request object
    :param id: the primary key of the selected course
    :return: HttpResponse 200 containing the HTML as body
    """
    obj = get_object_or_404(Course, pk=id)
    courses = list(obj.old_courses.all())
    courses.append(obj)
    items = {}
    for course in courses:
        for summary in course.summary_set.filter(accepted=True):
            if summary.year not in items:
                items[summary.year] = {'summaries': [], 'exams': [],
                                       'legacy': course if course.pk != obj.pk
                                       else None}
            items[summary.year]['summaries'].append({
                "year": summary.year,
                "name": f'{ _("Summary") } { summary.name }',
                "id": summary.id
            })
        for exam in course.exam_set.filter(accepted=True):
            if exam.year not in items:
                items[exam.year] = {'summaries': [], 'exams': [],
                                    'legacy': course if course.pk != obj.pk
                                    else None}
            items[exam.year]['exams'].append({
                "type": "exam",
                "year": exam.year, "name":
                    f"{ exam.get_type_display() } { exam.name }",
                "id": exam.id
            })

    return render(request, 'education/course.html',
                  {'course': obj, 'items': sorted(items.items(),
                                                  key=lambda x: x[0])})


@login_required
@membership_required
def exam(request, id):
    """
    Fetches and outputs the specified exam

    :param request: the request object
    :param id: the id of the exam
    :return: 302 if not authenticated else 200 with the file as body
    """
    exam = get_object_or_404(Exam, id=int(id))

    exam.download_count += 1
    exam.save()

    ext = os.path.splitext(exam.file.path)[1]
    filename = f'{ exam.course.name }-exam{ exam.year }{ ext }'
    return sendfile(request, exam.file.path,
                    attachment=True, attachment_filename=filename)


@login_required
@membership_required
def summary(request, id):
    """
    Fetches and outputs the specified summary

    :param request: the request object
    :param id: the id of the summary
    :return: 302 if not authenticated else 200 with the file as body
    """
    obj = get_object_or_404(Summary, id=int(id))

    obj.download_count += 1
    obj.save()

    ext = os.path.splitext(obj.file.path)[1]
    filename = f'{ obj.course.name }-summary{ obj.year }{ ext }'
    return sendfile(request, obj.file.path,
                    attachment=True, attachment_filename=filename)


@login_required
def submit_exam(request, id=None):
    """
    Renders the form to submit a new exam

    :param request: the request object
    :param id: the course id (optional)
    :return: 302 if not authenticated else 200 with the form HTML as body
    """
    saved = False

    if request.POST:
        form = AddExamForm(request.POST, request.FILES)
        if form.is_valid():
            saved = True
            obj = form.save(commit=False)
            obj.uploader = request.member
            obj.uploader_date = datetime.now()
            obj.save()

            form = AddExamForm()
    else:
        obj = Exam()
        obj.exam_date = date.today()
        if id is not None:
            obj.course = Course.objects.get(id=id)
        form = AddExamForm(instance=obj)

    return render(request, 'education/add_exam.html',
                  {'form': form, 'saved': saved})


@login_required
def submit_summary(request, id=None):
    """
    Renders the form to submit a new summary

    :param request: the request object
    :param id: the course id (optional)
    :return: 302 if not authenticated else 200 with the form HTML as body
    """
    saved = False

    if request.POST:
        form = AddSummaryForm(request.POST, request.FILES)
        if form.is_valid():
            saved = True
            obj = form.save(commit=False)
            obj.uploader = request.member
            obj.uploader_date = datetime.now()
            obj.save()

            obj = Summary()
            obj.author = request.member.get_full_name()
            form = AddSummaryForm(instance=obj)
    else:
        obj = Summary()
        if id is not None:
            obj.course = Course.objects.get(id=id)
        obj.author = request.member.get_full_name()
        form = AddSummaryForm(instance=obj)

    return render(request, 'education/add_summary.html',
                  {'form': form, 'saved': saved})


@login_required
def books(request):
    """
    Renders a page with information about book sale
    Only available to members and to-be members

    :param request: the request object
    :return: 403 if no active membership else 200 with the page HTML as body
    """
    if (request.member and request.member.is_authenticated and
        (request.member.current_membership or
         (request.member.earliest_membership and
          request.member.earliest_membership.since > timezone.now().date())
         )):
        return render(request, 'education/books.html')
    raise PermissionDenied
