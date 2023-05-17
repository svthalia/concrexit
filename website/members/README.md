# Members
The members app forms the member administration of Thalia.

## Members
Members are a proxy model for the default Django `User` model.
This means that all fields of the `User` model are also available on the `Member` model.
We do not have a separate user model.
This is a choice we made, and it has some advantages and disadvantages.
Migrating this is nearly impossible, so we will stick with this for now.

## Member profiles
In order to store additional information about members, we have a `MemberProfile` model, which is linked to the `Member` model using a `OneToOneField`.
This means that after you create a `Member`, you also have to create a `MemberProfile` for them if you want them to be able to do anything useful on the website.
Users without a `MemberProfile` can still log in, but they cannot do anything useful.
This can be used for certain functional accounts.
In the future, we might want to implement something special for such accounts, but for now we just use this.

Note that members have a profile that they can edit themselves. They can upload an avatar and change certain information about themselves.
This is one of the few places where users can send their own data to the server, so we have to be careful about this.
People tend to find ways to break things in this app.

## Memberships
Memberships are used to keep track of the history of memberships of members.
We implement the rules and regulations of Thalia in this model.

## Email changes
Members can change their email address.
This requires them to verify their new email address.
This is implemented using a `EmailChange` model.

## Other functionality
Apart from a member list view, allowing people to see who is a member of Thalia, there is not much more functionality in this app.
Rather, this app implements some features that are used by other apps, like decorators.

## Privacy
This app is one of the most important apps for privacy.
It contains a lot of personal data, and we have to be careful with this.
We have to make sure that we do not leak any personal data, and that we do not store any data that we do not need.
We can improve on this quite a bit, but we are not doing too bad.
