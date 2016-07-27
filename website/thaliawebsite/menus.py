from django.utils.translation import ugettext as _

main = [
    {'title': _('Home'), 'name': 'index'},
    {'title': _('Association'), 'name': '#', 'submenu': [
        {'title': _('Board'), 'name': '#'},
        {'title': _('Committees'), 'name': '#'},
        {'title': _('Members'), 'name': '#'},
        {'title': _('Documents'), 'name': 'documents:index'},
        {'title': _('Members'), 'name': '#'},
        {'title': _('Sister Associations'), 'name': 'sister-associations'},
        {'title': _('Become Member'), 'name': '#'},
        {'title': _('Thabloid'), 'name': '#'},
    ]},
    {'title': _('For Members'), 'name': '#', 'submenu': [
        {'title': _('Photos'), 'name': '#'},
        {'title': _('Statistics'), 'name': '#'},
        {'title': _('Become Active'), 'name': 'become-active'},
        {'title': _('Wiki'), 'name': '#'},
    ]},
    {'title': _('Calendar'), 'name': '#'},
    {'title': _('Career'), 'name': '#', 'submenu': [
        {'title': _('Sponsor'), 'name': '#'},
        {'title': _('Vacancies'), 'name': '#'},
    ]},
    {'title': _('Education'), 'name': '#', 'submenu': [
        {'title': _('Book Sale'), 'name': '#'},
        {'title': _('Course Overview'), 'name': '#'},
        {'title': _('Add Exam'), 'name': '#'},
        {'title': _('Add Summary'), 'name': '#'},
    ]},
    {'title': _('Contact'), 'name': 'contact'},
]
