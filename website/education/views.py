import itertools
import os
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from sendfile import sendfile

from .forms import AddExamForm, AddSummaryForm
from .models import Category, Course, Exam, Summary


def courses(request):
    categories = Category.objects.all()
    objects = Course.objects.order_by('name_' + request.LANGUAGE_CODE).filter(
        until=None)
    return render(request, 'education/courses.html',
                  {'courses': objects, 'categories': categories})


def course(request, id):
    obj = get_object_or_404(Course, pk=id)
    courses = list(obj.old_courses.all())
    courses.append(obj)
    items = []
    for course in courses:
        items = itertools.chain(items,
                                ({"type": "summary", "year": x.year,
                                  "name": "{} {}".format(_("Summary"),
                                                         x.name),
                                  "id": x.id,
                                  "course": course}
                                 for x in course.summary_set.filter(
                                    accepted=True)))
        items = itertools.chain(items,
                                ({"type": "exam", "year": x.year, "name":
                                    "{} {}".format(
                                        dict(Exam.EXAM_TYPES)[x.type], x.name),
                                  "id": x.id, "course": course}
                                 for x in
                                 course.exam_set.filter(accepted=True)))

    return render(request, 'education/course.html',
                  {'course': obj, 'items': items})


def student_participation(request):
    return render(request, 'education/student_participation.html')


@login_required
def exam(request, id):
    exam = get_object_or_404(Exam, id=int(id))
    ext = os.path.splitext(exam.file.path)[1]
    filename = '{}-exam{}{}'.format(exam.course.name, exam.year, ext)
    return sendfile(request, exam.file.path,
                    attachment=True, attachment_filename=filename)


@login_required
def summary(request, id):
    obj = get_object_or_404(Summary, id=int(id))
    ext = os.path.splitext(obj.file.path)[1]
    filename = '{}-summary{}{}'.format(obj.course.name, obj.year, ext)
    return sendfile(request, obj.file.path,
                    attachment=True, attachment_filename=filename)


@login_required
def submit_exam(request, id=None):
    saved = False

    if request.POST:
        form = AddExamForm(request.POST, request.FILES)
        if form.is_valid():
            saved = True
            obj = form.save(commit=False)
            obj.uploader = request.user
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
    saved = False

    if request.POST:
        form = AddSummaryForm(request.POST)
        if form.is_valid():
            saved = True
            obj = form.save(commit=False)
            obj.uploader = request.user
            obj.uploader_date = datetime.now()

            obj = Summary()
            obj.year = datetime.now().year
            obj.author = request.user.get_full_name()
            form = AddSummaryForm(instance=obj)
    else:
        obj = Summary()
        if id is not None:
            obj.course = Course.objects.get(id=id)
        obj.year = datetime.now().year
        obj.author = request.user.get_full_name()
        form = AddSummaryForm(instance=obj)

    return render(request, 'education/add_summary.html',
                  {'form': form, 'saved': saved})


@login_required
def books(request):
    return render(request, 'education/books.html')
