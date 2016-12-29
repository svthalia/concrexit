import datetime

from django.conf import settings
from django.forms import (ChoiceField, DateField, ModelChoiceField,
                          ModelForm, SelectDateWidget)

from .models import Course, Exam, Summary


class AddExamForm(ModelForm):
    this_year = datetime.date.today().year
    years = list(reversed(range(this_year - 8, this_year + 1)))

    exam_date = DateField(
        widget=SelectDateWidget(years=years),
        initial=datetime.date.today
    )
    course = ModelChoiceField(
        queryset=Course.objects.order_by('name_' + settings.LANGUAGE_CODE),
        empty_label=None)
    type = ChoiceField(choices=Exam.EXAM_TYPES)

    class Meta:
        model = Exam
        fields = ('file', 'course', 'type', 'exam_date')


class AddSummaryForm(ModelForm):
    course = ModelChoiceField(
        queryset=Course.objects.order_by('name_' + settings.LANGUAGE_CODE),
        empty_label=None)

    class Meta:
        model = Summary
        fields = ('name', 'year', 'file', 'course', 'author')
