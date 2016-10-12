# Data migrations

The old new website of Study Association Thalia contained a lot of data.
Before we can launch the new website, all old data has to be migrated
to the new website.
The migration instructions for each part of the website are shown below.

## Active members

This is taken care of during member migration.

## Documents

## Education

## Events

## Mailing lists

Make sure that the API key is available as `MIGRATION_KEY` in settings.py.

To migrate the mailinglists, make sure that members, committees and boards
have been migrated. Then simply execute `python manage.py migratelists`.

## Members

To migrate members, committees, boards, memberships of committees and boards,
as well as introductionmentorships, execute `python manage.py migratemembers`.

Unfortunately, not all the data is complete. Most notably, some begin-dates are
missing. This will need to be fixed manually. These have been set to 1970,
as start dates are not optional.

This migration typically takes a few minutes.

## Newsletters

## Partners

## Photos

## Pizzas

## Thabloids

## Merchandise
