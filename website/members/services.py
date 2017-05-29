from datetime import date


def member_achievements(member):
    memberships = member.committeemembership_set.all()
    achievements = {}
    for membership in memberships:
        period = {
            'since': membership.since,
            'until': membership.until,
            'chair': membership.chair
        }

        if hasattr(membership.committee, 'board'):
            period['role'] = membership.role

        if (membership.until is None and
                hasattr(membership.committee, 'board')):
            period['until'] = membership.committee.board.until

        name = membership.committee.name
        if achievements.get(name):
            achievements[name]['periods'].append(period)
            if achievements[name]['earliest'] > membership.since:
                achievements[name]['earliest'] = membership.since
            achievements[name]['periods'].sort(key=lambda x: x['since'])
        else:
            achievements[name] = {
                'name': name,
                'periods': [period],
                'earliest': membership.since,
            }
    mentor_years = member.mentorship_set.all()
    for mentor_year in mentor_years:
        name = "Mentor in {}".format(mentor_year.year)
        # Ensure mentorships appear last but are sorted
        earliest = date.today()
        earliest = earliest.replace(year=earliest.year + mentor_year.year)
        if not achievements.get(name):
            achievements[name] = {
                'name': name,
                'earliest': earliest,
            }
    return sorted(achievements.values(), key=lambda x: x['earliest'])
