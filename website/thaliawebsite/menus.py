"""
This file defines the menu layout.

We set the variable `:py:main` to form the menu tree.
"""

from django.utils.translation import ugettext_lazy as _

__all__ = ['MAIN_MENU']

"""
Defines the menu layout as a nested dict

The authenticated key indicates something should only
be visible for logged-in users. *Do not* rely on that for authentication!
"""
MAIN_MENU = [
    {'title': 'Home', 'name': 'index'},
    {
        'title': _('Association'),
        'submenu': [
            {'title': _('Board'), 'name': 'activemembers:boards'},
            {'title': _('Committees'), 'name': 'activemembers:committees'},
            {'title': _('Societies'), 'name': 'activemembers:societies'},
            {'title': _('Documents'), 'name': 'documents:index'},
            {'title': _('Merchandise'), 'name': 'merchandise:index'},
            {'title': _('Sibling Associations'),
             'name': 'sibling-associations'},
            {'title': _('Become a Member'), 'name': 'registrations:index'},
            {'title': _('Thabloid'), 'name': 'thabloid:index'},
            {'title': _('Alumni'), 'name': 'alumni'},
        ],
    },
    {
        'title': _('For Members'),
        'submenu': [
            {'title': _('Member list'), 'name': 'members:index'},
            {'title': _('Photos'), 'name': 'photos:index'},
            {'title': _('Statistics'), 'name': 'statistics'},
            {'title': _('Styleguide'), 'name': 'styleguide'},
            {'title': _('Become Active'), 'name': 'become-active'},
            {'title': _('Wiki'), 'url': '/wiki/', 'authenticated': True},
        ],
    },
    {
        'title': _('Calendar'),
        'name': 'events:index',
    },
    {
        'title': _('Career'),
        'submenu': [
            {'title': _('Partners'), 'name': 'partners:index'},
            {'title': _('Vacancies'), 'name': 'partners:vacancies'},
        ],
    },
    {
        'title': _('Education'),
        'submenu': [
            {
                'title': _('Summaries & Exams'),
                'name': 'education:courses',
                # TODO: Remove submenu when the new template is implemented
                # everywhere
                'submenu': [
                    {
                        'title': _('Submit Exam'),
                        'name': 'education:submit-exam'
                    },
                    {
                        'title': _('Submit Summary'),
                        'name': 'education:submit-summary'
                    },
                ],
            },
            {'title': _('Book Sale'), 'name': 'education:books'},
            {
                'title': _('Student Participation'),
                'name': 'education:student-participation'
            },
        ]
    },
    {'title': _('Contact'), 'name': 'contact'},
]
