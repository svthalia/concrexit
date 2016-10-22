import os

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from django.utils.text import slugify

from photos.models import Album, Photo


class Command(BaseCommand):
    help = ("Imports a photo album based on a directory of images. "
            "This is done per album, to avoid having to have sufficient "
            "storage space available for two copies of every album.")

    def add_arguments(self, parser):
        parser.add_argument('folder', help='Specify album folder.')

    def handle(self, *args, **options):
        if not os.path.isdir(options['folder']):
            raise Exception("You must specify a directory to import")

        foldername = os.path.relpath(options['folder'])
        album, date, title = foldername.split('_')
        date = parse_date('{}-{}-{}'.format(date[:4], date[4:6], date[6:]))
        slug = slugify('-'.join([str(date), title]))

        if Album.objects.filter(title=title, date=date).exists():
            print("An album with title ({}) and date ({}) already exists."
                  .format(title, date))
            return

        print("Importing album '{}' ({})".format(title, str(date)))
        album = Album(title=title, date=date, slug=slug)
        album.save()

        n = 0
        for filename in os.listdir(options['folder']):
            try:
                photo = Photo(album=album)
                file = open(os.path.join(options['folder'], filename), 'rb')
                photo.file.save(filename, File(file))
                photo.save()
                n += 1
            except Exception:
                print("Could not import {}".format(filename))

        print("Imported {} photos from {}".format(n, options['folder']))
