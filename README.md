Thalia Website
==============

New new Thalia website, now with extra Django.

    #Concrexit

Getting started
---------------

0. Get at least Python 3.4 and install the Pillow requirements as per below.
   Also make sure that you have `lessc` installed (see below).
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

    apt-get install python-dev gettext gcc build-essential libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

For other operating systems, see the [Pillow Documentation][pillow-install].


[pillow-install]: https://pillow.readthedocs.io/en/latest/installation.html

NodeJS dependencies
-----------------------
1. `lessc`:
   * For Ubuntu  use: `apt-get install node-less`
