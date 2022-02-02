"""This file defines the menu layout.

We set the variable `:py:main` to form the menu tree.
"""
from django.utils.translation import gettext_lazy as _

__all__ = ["MAIN_MENU"]

"""
Defines the menu layout as a nested dict

The authenticated key indicates something should only
be visible for logged-in users. *Do not* rely on that for authentication!
"""
MAIN_MENU = [
    {"title": "Home", "name": "index"},
    {
        "title": _("Association"),
        "submenu": [
            {"title": _("Board"), "name": "activemembers:boards"},
            {"title": _("Committees"), "name": "activemembers:committees"},
            {"title": _("Societies"), "name": "activemembers:societies"},
            {"title": _("Documents"), "name": "documents:index"},
            {"title": _("Merchandise"), "name": "merchandise:index"},
            {
                "title": _("Sibling Associations"),
                "name": "singlepages:sibling-associations",
            },
            {"title": _("Become a Member"), "name": "registrations:index"},
            {"title": _("Alumni"), "name": "events:alumni"},
        ],
    },
    {
        "title": _("For Members"),
        "submenu": [
            {"title": _("Member list"), "name": "members:index"},
            {"title": _("Photos"), "name": "photos:index"},
            {"title": _("Statistics"), "name": "members:statistics"},
            {"title": _("Styleguide"), "name": "singlepages:styleguide"},
            {"title": _("Thabloid"), "name": "thabloid:index"},
            {"title": _("Become Active"), "name": "singlepages:become-active"},
            {
                "title": _("G Suite Knowledge Base"),
                "url": "https://gsuite.members.thalia.nu/",
                "authenticated": True,
            },
        ],
    },
    {
        "title": _("Calendar"),
        "name": "events:index",
    },
    {
        "title": _("Career"),
        "submenu": [
            {"title": _("Partners"), "name": "partners:index"},
            {"title": _("Vacancies"), "name": "partners:vacancies"},
        ],
    },
    {
        "title": _("Education"),
        "submenu": [
            {
                "title": _("Summaries & Exams"),
                "name": "education:courses",
            },
            {"title": _("Book Sale"), "name": "education:books"},
            {
                "title": _("Student Participation"),
                "name": "education:student-participation",
            },
        ],
    },
    {"title": _("Contact"), "name": "singlepages:contact"},
]
