from django.utils.translation import ugettext_lazy as _

main = [
    {'title': _('Home'), 'name': 'index'},
    {'title': _('Association'), 'name': '#', 'submenu': [
        {'title': _('Board'), 'name': 'activemembers:board'},
        {'title': _('Committees'), 'name': 'activemembers:committees'},
        {'title': _('Members'), 'name': 'members:index'},
        {'title': _('Documents'), 'name': 'documents:index'},
        {'title': _('Merchandise'), 'name': 'merchandise:index'},
        {'title': _('Members'), 'name': 'members:index'},
        {'title': _('Sister Associations'), 'name': 'sister-associations'},
        {'title': _('Become a Member'), 'name': 'become-a-member'},
        {'title': _('Thabloid'), 'name': 'thabloid:index'},
    ]},
    {'title': _('For Members'), 'name': '#', 'authenticated': True,
        'submenu': [
        {'title': _('Photos'), 'name': 'photos:index'},
        {'title': _('Statistics'), 'name': '#'},
        {'title': _('Become Active'), 'name': 'become-active'},
        {'title': _('Wiki'), 'url': '/wiki/'},
    ]},
    {'title': _('Calendar'), 'name': '#'},
    {'title': _('Career'), 'name': 'partners:index', 'submenu': [
        {'title': _('Partners'), 'name': 'partners:index'},
        {'title': _('Vacancies'), 'name': 'partners:vacancies'},
    ]},
    {'title': _('Education'), 'name': '#', 'submenu': [
        {'title': _('Book Sale'), 'name': '#'},
        {'title': _('Course Overview'), 'name': '#'},
        {'title': _('Submit Exam'), 'name': '#'},
        {'title': _('Submit Summary'), 'name': '#'},
    ]},
    {'title': _('Contact'), 'name': 'contact'},
]
