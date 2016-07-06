Thalia Website
==============

New new Thalia website, now with extra Django.

    #Concrexit

Getting started
---------------

0. Get at least Python 3.4
1. Clone this repository
2. Run `source ./source_me.sh` (or use your own favourite virtualenv solution)
3. Run `pip install -r requirements.txt`
4. Run `pip install -r dev-requirements.txt`
5. `cd website`
6. `./manage.py migrate` to initialise the database
7. `./manage.py runserver` to run a testing server

Testing and linting
-------------------

1. In the root folder of the project, run `tox`.
