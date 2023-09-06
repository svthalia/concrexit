# Active members

This app is used to manage the active members of Thalia. Specifically, it defines MemberGroups: Boards, Committees and Societies.
Additionally, it defines Mentorships for the orientation week.

## MemberGroups
MemberGroups can be active or inactive. Active MemberGroups are shown on the website.
Inactive MemberGroups are not shown on the website, but are still available in the admin interface, mainly for historical archiving purposes.

### Authentication backend (though technically authorization backend)
We have defined a custom authentication backend, `MemberGroupBackend`, allowing us to give committees certain permissions.
Only active members receive these permissions.

## MemberGroupMembership
Group memberships are managed through the admin interface.
Note that we want to keep the history of group memberships, so we do not delete memberships when they are no longer active.
Instead, we set the `end_date` field of the membership to the date when the membership ended.
This way, we can still see the history of group memberships for each member.

Note that this complicates the admin interface: it is not easy to switch roles, because you have to set the `end_date` of the old membership and create a new membership.
We did not feel like implementing a custom admin interface for this, as only few people use this interface.

### Role
The chair of a MemberGroup is determined by the `chair` field of the MemberGroup model.
There can only be one chair at a time.

Apart from being a chair, each membership can have a role. This is a free text field, so it can be anything.
For example, the role of a board member could be "Chairman", "Secretary", "Treasurer", etc.
This is a bit of feature creep, but in certain situations is useful to have this information available, and it is not too hard to implement.

Note that we do not want to implement separate models for this role. The active members app is a core functionality of the website, and we do not want to make it too complicated.
Features should be used for multiple years, and typically the way roles in member groups are defined changes every few years.
The `chair` field is an exception, because it is an official position within the association (according to the articles of association / rules and regulations).

### is_staff
When a user becomes a member of a MemberGroup, their `is_staff` field is set to `True`.
This means that they can access the admin interface of the website.
Based on the permissions, they can access certain parts of the admin interface (so technically, it is possible to get access to the admin interface, but don't see anything because you don't have permissions).

When a user is no longer a member of any MemberGroup, their `is_staff` field is not set to `False` automatically, because this might be in the future (so there is no signal for this).
Instead, we periodically check which users are no longer a member of any MemberGroup, and set their `is_staff` field to `False` (using the `revoke_staff` management command).

## GSuite
Active members are synced to GSuite (Google Workspace) using the [GSuite API](https://developers.google.com/admin-sdk/directory).
Every active member receives a GSuite account in the `members.thalia.nu` domain (using their Thalia username).
This is determined by the `is_staff` field of the `User` model.
Whenever a user's `is_staff` field is set to `True`, a GSuite account is created for them (with a random password).
These credentials are then sent to the user via email.

When a user's `is_staff` field is set to `False`, their GSuite account is suspended.
This means that the user can no longer log in to their account, but their data is still available.
Users also receive an email when their account is suspended.

Periodically, we remove all suspended accounts from GSuite (using the `delete_gsuite_users` management command).
