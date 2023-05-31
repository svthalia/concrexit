# Promotion requests
The `promotion` app is a simple app that allows committee members to request promo material for their events, and
for the committee responsible for promotion to manage these requests to keep track of what has been requested and
who is working on it.

## How does it work?
The app consists of a single model, `PromoRequest`. An admin inline is added to the `Event` admin page to allow
committee members to request promo material for their events. `PromoRequest`s can also be created manually via
the admin interface, without an event.

Periodically, emails are sent to an email address, specified in `settings.py` to notify them of new promo requests.
This used to be done on every request, but this was changed to a periodic task to prevent spamming.

The `PromoRequest` model has a `status` field and an `assigned_to` field, for keeping track of the status of the
request and who is working on it. The `drive_folder` URL field can be used to keep track of the Google Drive folder
where the promo material is stored.

## Why is this included in concrexit?
There has been a lot of discussion about whether this app should be included in concrexit or not.
It is an internal tool that has no use for general members, and it is not a core part of the association, so this
goes right against the philosophy of what concrexit should be.

The main reason why this app is included in concrexit is that it is a very simple app, that is very easy to maintain
(as long as we do not add too many features to it). Moreover, promo requests are very closely related to events and are
made by a lot of committees, so it makes sense to have it in the same system as the `events` app.
An external tool to manage promo requests, though easier to maintain, would be a lot more inconvenient to use for
committee members organizing events. Publishing events on concrexit is already standard procedure, so it makes sense
to have promo requests in the same place.

Note that to keep the app simple, we do not want to add too many features to it. The main functionality of the app is
to allow committee members to request promo material for their events, not for the promotion committee to keep track
of what they are doing. The latter is a nice-to-have, but not a core feature of the app. For this reason, for example,
the `assigned_to` field is a simple `CharField` instead of a `ForeignKey` to a `Member`.

## Ambitions
No new features should be added to this app. It should be kept as simple as possible. If new features are needed,
the committee responsible for promotion should use a separate tool for this (and integrate it with concrexit if needed,
pushing new promo requests from concrexit via an API to this separate tool).

In order to keep the app simple, we should **not** implement syncing with Google Drive (for example, to automatically
create a folder for each promo request). This is a nice-to-have, but not a core feature of the app that does not fit the
philosophy on the scope of concrexit.
