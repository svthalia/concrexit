# Shortlinks

This is a simple Django app to create shortlinks for the Thalia website.
A shortlink is a link that redirects to another link, but is shorter so we can use `https://thalia.nu/shortlink`.
We can link both to internal and external links.
The idea is that external links are not redirected directly, but through a page on our website, so users can see where they are going.
However, we do not enforce this.

Shortlinks are created using the Django admin interface.
The path is resolved after all other paths, so it is not possible to create shortlinks that override paths that other apps define.
