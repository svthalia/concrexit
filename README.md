Thalia Website
==============

New new Thalia website, now with extra Django.

    #Concrexit



[![build status](https://gitlab.science.ru.nl/thalia/concrexit/badges/master/build.svg)](https://gitlab.science.ru.nl/thalia/concrexit/commits/master)
[![coverage report](https://gitlab.science.ru.nl/thalia/concrexit/badges/master/coverage.svg?job=python35)](https://gitlab.science.ru.nl/thalia/concrexit/commits/master)



Getting started
---------------

If you use Docker, please look at [this part](#docker) of the README.

0. Get at least Python 3.4 and install the Pillow requirements as per below.
1. Clone this repository
2. Run `source ./source_me.sh` (or use your own favourite virtualenv solution)
3. Run `pip install -r requirements.txt`
4. Run `pip install -r dev-requirements.txt`
5. `cd website`
6. `./manage.py migrate` to initialise the database
7. `./manage.py createsuperuser` to create the first user (note that this user won't be a member!)
8. `./manage.py runserver` to run a testing server

Testing and linting
-------------------

1. In the root folder of the project, run `tox`.

You may get errors about missing interpreters. That is normal and can be 
ignored. If you want to run a specific check, you can do the following:

    tox -e flake8  # Runs the flake8 linter
    tox -e py34    # runs the tests with python 3.4
    tox -e py35    # runs the tests with python 3.5

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

1. `./manage.py makemessages <appname>`
2. This will create or update the files under `<appname>/locale/`.
3. Use poedit (or your favourite tool -- please do not use a plain text editor since those cannot handle all the subtleties) to fix the translations.
4. `./manage.py compilemessages`

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
