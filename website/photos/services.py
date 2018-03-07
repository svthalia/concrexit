from django.db.models import When, Value, BooleanField, ExpressionWrapper, Q, \
    Case


def is_album_accessible(request, album):
    if request.member and request.member.current_membership is not None:
        return True
    elif request.member and request.member.current_membership is None:
        # This user is currently not a member, so need to check if he/she
        # can view this album by checking the membership
        filter = Q(since__lte=album.date) & Q(until__gte=album.date)
        return request.member.membership_set.filter(filter).count() > 0
    return False


# Annotate the albums which are accessible by the user
def get_annotated_accessible_albums(request, albums):
    if request.member and request.member.current_membership is None:
        # The user is currently not a member
        # so only show photos that were made during their membership
        albums_filter = Q(pk__in=[])
        for membership in request.member.membership_set.all():
            if membership.until is not None:
                albums_filter |= (Q(date__gte=membership.since) & Q(
                    date__lte=membership.until))
            else:
                albums_filter |= (Q(date__gte=membership.since))

        albums = albums.annotate(accessible=Case(
            When(albums_filter, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()))
    else:
        # The user is currently a member, so show all albums
        albums = albums.annotate(accessible=ExpressionWrapper(
            Value(True), output_field=BooleanField()))

    return albums
