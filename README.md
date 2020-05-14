Thalia Website 
==============

[![Linting and Testing](https://github.com/svthalia/concrexit/workflows/Linting%20and%20Testing/badge.svg)](https://github.com/svthalia/concrexit/actions)
[![coverage](https://img.shields.io/badge/coverage-view-important)](https://thalia-coverage.s3.amazonaws.com/master/index.html)
[![documentation](https://img.shields.io/badge/documentation-view-blueviolet)](https://thalia-documentation.s3.amazonaws.com/master/index.html)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code Climate](https://codeclimate.com/github/svthalia/concrexit/badges/gpa.svg)](https://codeclimate.com/github/svthalia/concrexit)

The latest Thalia Website built on Django.

Getting started
---------------

If you use Docker, please look at [this part](#docker) of the README.

0. Get at least Python 3.7 and install poetry and the Pillow requirements as per below.
1. Clone this repository
2. Make sure `poetry` uses your Python 3.x installation: `poetry env use python3`
3. Run `poetry install`
4. Run `poetry shell`
5. `cd website`
6. `./manage.py migrate` to initialise the database
7. `./manage.py createsuperuser` to create the first user (note that this user won't be a member!)
8. `./manage.py createfixtures -a` to generate a bunch of test data
9. `./manage.py runserver` to run a testing server
10. Go to the user you created and complete the profile and add a membership for full access

Testing and linting
-------------------

You can use [`pyenv`](https://github.com/pyenv/pyenv) (on Unix systems) to test in different python
environments.

All code has to be run through [`black`](https://github.com/psf/black) before being committed. To black the code before committing make run `black` one the base directory of this project.
If you want to integrate `black` with your editor look in the [`black` docs](https://black.readthedocs.io/en/stable/editor_integration.html). On linux you can find the black executable in `~/.cache/poety/virtualenvs/<your env>/bin/black`.

There are a range of tests that can be run:

    poetry run python website/manage.py check
    poetry run python website/manage.py templatecheck --project-only
    poetry run python website/manage.py makemigrations --no-input --check --dry-run
    poetry run coverage run website/manage.py test website/
    poetry run coverage report

poetry
------

Install poetry per the [poetry documentation][poetry install]. Make sure you install at least version 1.x.x.

[poetry install]: https://github.com/sdispater/poetry#installation

Pillow dependencies
-------------------

For Ubuntu 18.04, use:

    apt-get install python3-dev gettext gcc build-essential libtiff5-dev libjpeg-turbo8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

Or try:

    apt-get build-dep python3-pil

For other operating systems, see the [Pillow Documentation][pillow-install].


[pillow-install]: https://pillow.readthedocs.io/en/latest/installation.html


On macOS you will also need to install `libmagic`, using the brew package manager by running `brew install libmagic`.

Thabloid dependencies
---------------------

To be able to generate JPGs from PDFs, we need ghostscript:

    apt-get install ghostscript

Or for macOS:

    brew install ghostscript

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

Settings
------------------

The settings of our project are located in `website/thaliawebsite/settings`.
This is a Python module that loads the included settings files based on the environment you are running in.

- If `DJANGO_PRODUCTION` is set in the environment `production.py` will be included
- If `GITHUB_ACTIONS` is set in the environment `testing.py` will be included
- If `localsettings.py` exists it will be included, you can use this to override settings on your local development server without the risk of committing secrets.

`settings.py` contains the default included settings.

Documentation
------------------

The documentation for our code is located inside the files and is combined using [Sphinx](https://www.sphinx-doc.org/en/master/) into an HTML output.
The continuous integration checks if the latest Python modules are included in the Sphinx files located in the `docs` folder

To update these files:

1. `cd docs` into the application's directory
2. Run `poetry install -E docs` to install the dependencies
3. Run `./generate-apidocs.sh` to update the `.rst` documents

If you have a `localsettings.py` then make sure you do not commit this part of the documentation to version control.

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
