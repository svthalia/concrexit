******
Media & Thumbnailing
******

This document explains how the `utils.media` package enables us to serve public
and private media (user-uploaded) files. We also give an outline of the
workings of our thumbnailing implementation.

Media types
===========

We differentiate between two types of media: public and private. Public means
that the files can be served without any kind of authentication. Requests for
private files have to be checked by Django first before we offload serving
the file using [django-sendfile2](https://github.com/moggers87/django-sendfile2).

Public
------


The public files are saved in `MEDIA_ROOT/public/`.
These files can be served by nginx like one would with a regular
[`MEDIA_ROOT`](https://docs.djangoproject.com/en/2.1/ref/settings/#media-root).
The files should be served at `MEDIA_URL/public/`.

Private
-------

The private files are saved in `MEDIA_ROOT` where the `public` folder is
the exception. This is a legacy implementation from our previous thumbnailing
code. We could decide to migrate these files to a dedicated `private` folder
in the future. Even though the files are not saved in such a folder they
are located at `MEDIA_URL/private/`. This path should be available to concrexit
so that the media files can be served correctly: the signature
(more on that below) should be valid and match the path.

Signatures
----------

To make sure the private media files stay private we have implemented a
signature-based security mechanism based on the idea behind the
[Thumbor](https://thumbor.readthedocs.io/en/latest/security.html)'s security
implementation. This signature can be extended to contain more information,
like we did for our thumbnails.

The value of the signature, which is a dictionary, must at least contain
one key: `serve_path`. This is the path that is used in `utils.media.views.private_media()`
to determine the location of the media file that should be served. If this path
matches the path in the url the file will be made available to the user.
A second, optional, key is `attachment` which is used by the sendfile backend
to force a download if the value is `True`.

.. code-block:: python

    sig_info = { 'serve_path': f'{settings.MEDIA_ROOT}/<image location>' }
    print(signing.dumps(sig_info))
    'eyJzZXJ2ZV9wYXRoIjoiL21lZGlhLzxpbWFnZSBsb2NhdGlvbj4ifQ:1gsbnC:QJTqFUWY6HxMBTEIxYPl9V1yf48'

The signature is appended to the location using a query parameter with
the key `sig` and is valid for 3 hours as implemented by
`utils.media.views._get_image_information`.

.. code-block::

    https://<base url>/media/private/<image location>?sig=eyJzZXJ2ZV9wYXRoIjoiL21lZGlhLzx...

To get the url of a media item you can use `utils.media.services.get_media_url()`. **Never use this to get a url directly from user input!**

Thumbnails
==========

To make sure we do not have to serve full-size images to users every time they
open a page we decided to thumbnail our images. This functionality is provided
as a templatetag (`utils.templatetags.thumbnail`) and service (`utils.media.services.get_thumbnail_url()`).

Every thumbnail only needs to be generated once, when the thumbnail exists the
tools mentioned above will return the direct media url relative to the root of
the concrexit instance. If the image is private the url will contain the
signature as well.

If the thumbnail does not yet exist the returned url will be the url of the
generation function (`utils.media.views.generate_thumbnail`). This url can then
be called by the browser of the user creating the thumbnails on-demand preventing
blocking of the page or large workloads when uploading multiple photos at once.
Once the thumbnail is generated the user will be redirected to the real image.

The url to the thumbnail generation route is signed with a signature that
extends the signature we use to serve private media files. More information
about the signature can be found in the next section.

**The thumbnailing tools should never be used to create thumbnails from user
input directly!** They do not protect against directory traversel and assume
the path is correct. They are meant to be used with a path from an `ImageField`
or similar.

.. graphviz::

   digraph thumbnails {
        get[label="get_thumbnail_url"]
        generate[label="generate_thumbnail"]
        public[label="serve thumbnail as public media file"]
        private[label="serve thumbnail as private media file"]
        get -> generate [label="no thumbnail"]
        get -> public [label="thumbnail exists & is public"]
        get -> private [label="thumbnail exists & is private"]
        generate -> public [label="redirects"]
        generate -> private [label="redirects"]
   }


Signatures
----------

The signature used for the generation of thumbnails extends the signature to
load a private media file with keys used for the generation. The signature
contains all information required to generate the thumbnail.

.. code-block:: python

    {
        'visibility': 'public',
        'size': '300x300',
        'fit': 0,
        'path': 'image.jpeg',
        'thumb_path': 'thumbnails/300x300_0/image.jpeg',
        'serve_path': '/media/public/thumbnails/300x300_0/image.jpeg'
    }

The signature protects us against path tampering and thus path traversal and
DDoS attacks. We also know that a user can only get a valid signature if
they accessed a page providing them with that signature.
