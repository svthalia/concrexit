def is_owner(member, event_doc):
    if member and member.is_authenticated:
        if member.is_superuser or member.has_perm("documents.override_owner"):
            return True

        if event_doc and member.has_perm("documents.change_document"):
            return member.get_member_groups().filter(pk=event_doc.owner.pk).exists()

    return False
