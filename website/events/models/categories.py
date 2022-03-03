from django.utils.translation import gettext_lazy as _

CATEGORY_ALUMNI = "alumni"
CATEGORY_EDUCATION = "education"
CATEGORY_CAREER = "career"
CATEGORY_LEISURE = "leisure"
CATEGORY_ASSOCIATION = "association"
CATEGORY_OTHER = "other"

EVENT_CATEGORIES = (
    (CATEGORY_ALUMNI, _("Alumni")),
    (CATEGORY_EDUCATION, _("Education")),
    (CATEGORY_CAREER, _("Career")),
    (CATEGORY_LEISURE, _("Leisure")),
    (CATEGORY_ASSOCIATION, _("Association Affairs")),
    (CATEGORY_OTHER, _("Other")),
)
