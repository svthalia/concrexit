from django.utils.translation import ugettext_lazy as _

main = [
    {'title': _('Home'), 'name': 'index'},
    {'title': _('Association'), 'name': '#', 'submenu': [
        {'title': _('Board'), 'name': '#'},
        {'title': _('Committees'), 'name': 'committees:index'},
        {'title': _('Members'), 'name': '#'},
        {'title': _('Documents'), 'name': 'documents:index'},
        {'title': _('Merchandise'), 'name': 'merchandise:index'},
        {'title': _('Members'), 'name': '#'},
        {'title': _('Sister Associations'), 'name': 'sister-associations'},
        {'title': _('Become a Member'), 'name': 'become-a-member'},
        {'title': _('Thabloid'), 'name': '#'},
    ]},
    {'title': _('For Members'), 'name': '#', 'submenu': [
        {'title': _('Photos'), 'name': 'photos:index'},
        {'title': _('Statistics'), 'name': '#'},
        {'title': _('Become Active'), 'name': 'become-active'},
        {'title': _('Wiki'), 'name': '#'},
    ]},
    {'title': _('Calendar'), 'name': '#'},
    {'title': _('Career'), 'name': '#', 'submenu': [
        {'title': _('Sponsors'), 'name': '#'},
        {'title': _('Vacancies'), 'name': '#'},
    ]},
    {'title': _('Education'), 'name': '#', 'submenu': [
        {'title': _('Book Sale'), 'name': '#'},
        {'title': _('Course Overview'), 'name': '#'},
        {'title': _('Submit Exam'), 'name': '#'},
        {'title': _('Submit Summary'), 'name': '#'},
    ]},
    {'title': _('Contact'), 'name': 'contact'},
]
