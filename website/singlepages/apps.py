from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SinglepagesConfig(AppConfig):
    name = "singlepages"
    verbose_name = _("Singlepages")

    def menu_items(self):
        return {
            "categories": [
                {"name": "association", "title": "Association", "key": 1},
                {"name": "members", "title": "For Members", "key": 2},
                {"name": "education", "title": "Education", "key": 5},
            ],
            "items": [
                {
                    "category": "association",
                    "title": "Sibling Associations",
                    "viewname": "singlepages:sibling-associations",
                    "key": 5,
                },
                {
                    "category": "members",
                    "title": "Styleguide",
                    "viewname": "singlepages:styleguide",
                    "key": 4,
                },
                {
                    "category": "members",
                    "title": "Become Active",
                    "viewname": "singlepages:become-active",
                    "key": 6,
                },
                {
                    "category": "education",
                    "title": "Student Participation",
                    "viewname": "singlepages:student-participation",
                    "key": 2,
                },
                {
                    "category": "education",
                    "title": "Student well-being",
                    "viewname": "singlepages:student-well-being",
                    "key": 3,
                },
                {
                    "title": "Contact",
                    "viewname": "singlepages:contact",
                    "key": 6,
                },
            ],
        }
