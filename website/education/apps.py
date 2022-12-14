"""Configuration for the education package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EducationConfig(AppConfig):
    """AppConfig for the education package."""

    name = "education"
    verbose_name = _("Education")

    def menu_items(self):
        return {
            "categories": [{"name": "education", "title": "Education", "key": 5}],
            "items": [
                {
                    "category": "education",
                    "title": "Summaries & Exams",
                    "viewname": "education:courses",
                    "key": 0,
                },
                {
                    "category": "education",
                    "title": "Book Sale",
                    "viewname": "education:books",
                    "key": 1,
                },
            ],
        }
