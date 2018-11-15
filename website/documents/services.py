def is_owner(member, event_doc):
    if member and member.is_authenticated:
        if member.is_superuser:
            return True

        if event_doc:
            return member.get_member_groups().filter(
                    pk=event_doc.owner.pk).exists()

    return False
