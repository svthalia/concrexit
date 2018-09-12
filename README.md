Thalia Website
==============

New new Thalia website, now with extra Django.

    #Concrexit



[![build status](https://gitlab.science.ru.nl/thalia/concrexit/badges/master/build.svg)](https://gitlab.science.ru.nl/thalia/concrexit/commits/master)
[![coverage report](https://gitlab.science.ru.nl/thalia/concrexit/badges/master/coverage.svg)](https://gitlab.science.ru.nl/thalia/concrexit/commits/master)



Getting started
---------------

If you use Docker, please look at [this part](#docker) of the README.

0. Get at least Python 3.5 and install pipenv and the Pillow requirements as per below.
1. Clone this repository
2. Run `pipenv install --python 3 --dev`
3. Run `pipenv shell`
5. `cd website`
6. `./manage.py migrate` to initialise the database
7. `./manage.py createsuperuser` to create the first user (note that this user won't be a member!)
8. `./manage.py runserver` to run a testing server

Testing and linting
-------------------

1. In the root folder of the project, run `tox`.

You may get errors about missing interpreters. That is normal and can be
ignored. If you want to run a specific check, you can do the following:

    tox -e flake8           # Runs the flake8 linter
    tox -e py35-django20    # runs the tests with python 3.5 and Django 2.0
    tox -e py36-django20    # runs the tests with python 3.6 and Django 2.0

You can run `tox -l` to see the available environments.

Pipenv
------

Install Pipenv per the [pipenv documentation][pipenv install]

[pipenv install]: https://docs.pipenv.org/install/#installing-pipenv

Pillow dependencies
-------------------

For Ubuntu 16.04, use:

    apt-get install python3-dev gettext gcc build-essential libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

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
