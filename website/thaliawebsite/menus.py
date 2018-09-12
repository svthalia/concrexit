"""
This file defines the menu layout.

We set the variable `:py:main` to form the menu tree.
"""

from django.utils.translation import ugettext_lazy as _

__all__ = ['MAIN_MENU']

#: Defines the menu layout as a nested dict.
#:
#: The authenticated key indicates something should only
#: be visible for logged-in users. **Do not** rely on that for
#: authentication!
MAIN_MENU = [
    {'title': _('Home'), 'name': 'index'},
    {
        'title': _('Association'),
        'name': 'association',
        'submenu': [
            {'title': _('Board'), 'name': 'activemembers:boards'},
            {'title': _('Committees'), 'name': 'activemembers:committees'},
            {'title': _('Societies'), 'name': 'activemembers:societies'},
            {'title': _('Documents'), 'name': 'documents:index'},
            {'title': _('Merchandise'), 'name': 'merchandise:index'},
            {'title': _('Sister Associations'), 'name': 'sister-associations'},
            {'title': _('Become a Member'), 'name': 'registrations:index'},
            {'title': _('Thabloid'), 'name': 'thabloid:index'},
        ],
    },
    {
        'title': _('For Members'),
        'name': 'for-members',
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
        'submenu': [
            {'title': _('Order Pizza'), 'name': 'pizzas:index'},
        ],
    },
    {
        'title': _('Career'),
        'name': 'partners:index',
        'submenu': [
            {'title': _('Partners'), 'name': 'partners:index'},
            {'title': _('Vacancies'), 'name': 'partners:vacancies'},
        ],
    },
    {
        'title': _('Education'),
        'name': 'education:index',
        'submenu': [
            {'title': _('Book Sale'), 'name': 'education:books'},
            {
                'title': _('Student Participation'),
                'name': 'education:student-participation'
            },
            {
                'title': _('Course Overview'), 'name': 'education:courses',
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
        ]
    },
    {'title': _('Contact'), 'name': 'contact'},
]
