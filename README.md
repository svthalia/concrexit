Thalia Website [![coverage report](https://gitlab.science.ru.nl/thalia/concrexit/badges/master/coverage.svg)](https://gitlab.science.ru.nl/thalia/concrexit/commits/master)
==============

New new Thalia website, now with extra Django.

    #Concrexit


Getting started
---------------

If you use Docker, please look at [this part](#docker) of the README.

0. Get at least Python 3.6 and install poetry and the Pillow requirements as per below.
1. Clone this repository
2. Make sure `poetry` uses your python 3 installation: `poetry env use python3`
3. Run `poetry install`
4. Run `poetry shell`
5. `cd website`
6. `./manage.py migrate` to initialise the database
7. `./manage.py createsuperuser` to create the first user (note that this user won't be a member!)
8. `./manage.py createfixtures -a` to generate a bunch of test data
9. `./manage.py runserver` to run a testing server

Testing and linting
-------------------

You can use [`pyenv`](https://github.com/pyenv/pyenv) (on Unix systems) to test in different python
environments.

The linter can be run in the `poetry shell` or by running

    poetry run flake8 website

There are a range of tests that can be run:

    poetry run python manage.py check
    poetry run python manage.py templatecheck --project-only
    poetry run python manage.py makemigrations --no-input --check --dry-run
    poetry run python -mcoverage run --branch --source '.' manage.py test
    coverage report

poetry
------

Install poetry per the [poetry documentation][poetry install]

[poetry install]: https://github.com/sdispater/poetry#installation

Pillow dependencies
-------------------

For Ubuntu 18.04, use:

    apt-get install python3-dev gettext gcc build-essential libtiff5-dev libjpeg-turbo8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

Or try:

    apt-get build-dep python3-pil

For other operating systems, see the [Pillow Documentation][pillow-install].


[pillow-install]: https://pillow.readthedocs.io/en/latest/installation.html

Thabloid dependencies
---------------------

To be able to generate JPGs from PDFs, we need ghostscript:

    apt-get install ghostscript

Translating
------------------

Make sure to use British English.

To create translations for your app:

1. `cd` into the application's directory
2. `../manage.py makemessages --locale nl --no-obsolete`
3. This creates or updates `locale/nl/LC_MESSAGES/django.po`
4. Start poedit by calling `poedit locale/nl/LC_MESSAGES/django.po`
5. `../manage.py compilemessages` (should happen automatically when saving the file in poedit)
6. Commit both the `.po` and `.mo` file to the repository

Docker
------

First run with Docker:

1. `docker-compose up -d`
2. `docker-compose run web migrate`
3. `docker-compose run web createsuperuser`

Step 1. may take a while since `docker-compose` needs to retrieve all dependencies
and build the Docker images. Step 2. creates the necessary tables and step 3.
creates a superuser, as the command implies.

After step 3. you can access the Thalia website locally through http://localhost:8000/
