"""The forms defined by the education package."""
import datetime

from django.forms import (
    CharField,
    ChoiceField,
    ModelChoiceField,
    ModelForm,
    TypedChoiceField,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.snippets import datetime_to_lectureyear

from .models import Course, Exam, Summary


class AddExamForm(ModelForm):
    """Custom form to add exams, changes the possible years of the date."""

    this_year = datetime.date.today().year
    years = list(reversed(range(this_year - 8, this_year + 1)))

    course = ModelChoiceField(
        queryset=Course.objects.order_by("name"),
        empty_label=None,
    )
    type = ChoiceField(choices=Exam.EXAM_TYPES)

    class Meta:
        model = Exam
        fields = ("file", "course", "type", "language", "exam_date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exam_date"].widget.input_type = "date"


class AddSummaryForm(ModelForm):
    """Custom form to add summaries, orders courses by name and formats the year as lecture years."""

    course = ModelChoiceField(
        queryset=Course.objects.order_by("name"),
        empty_label=None,
    )

    this_year = datetime_to_lectureyear(timezone.now())
    years = reversed(
        [(x, f"{x} - {x + 1}") for x in range(this_year - 20, this_year + 1)]
    )

    year = TypedChoiceField(choices=years, coerce=int, empty_value=this_year)

    class Meta:
        model = Summary
        fields = ("name", "year", "language", "file", "course", "author")


class SummaryAdminForm(ModelForm):
    """Custom form for summaries so that we can show more data in the admin."""

    def __init__(self, data=None, files=None, **kwargs):
        super().__init__(data, files, **kwargs)
        obj = kwargs.get("instance", None)
        if not obj:
            self.fields["phone"].widget = self.fields["phone"].hidden_widget()
            self.fields["email"].widget = self.fields["email"].hidden_widget()
        else:
            self.fields["phone"].initial = obj.uploader.profile.phone_number
            self.fields["email"].initial = obj.uploader.email

    phone = CharField(label=_("Uploader phone"), disabled=True, required=False)
    email = CharField(label=_("Uploader email"), disabled=True, required=False)

    class Meta:
        model = Summary
        fields = "__all__"
