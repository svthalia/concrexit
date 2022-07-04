Code structure
==============

How is the website code structured?
-----------------------------------

We adhere to Django best practices, which basically consists of dividing code
up into modules, and using consistent filenames for the different parts in these
modules. You can read about this `here <https://masteringdjango.com/django-tutorials/mastering-django-structure/>`_.

Where can I find the code for this page?
----------------------------------------

The way to find the code for a page is to look in the root urls.py_. From there
on you can look at the specific urls.py of a package, and you will find the specific
view that renders the page you're looking for.

If you're looking at an admin page, it is a bit harder to find the code, but you will
have to look in the admin.py files. There is an admin class for (almost) each model
in the database. So your best bet is to find out which model you're looking for,
and then checking the admin class for that model.

.. _urls.py: https://github.com/svthalia/concrexit/blob/master/website/thaliawebsite/urls.py
