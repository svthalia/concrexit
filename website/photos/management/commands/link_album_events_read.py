import csv
import sys

from django.core.management.base import BaseCommand

from events.models import Event
from photos.models import Album


# todo: maybe import-export?
class Command(BaseCommand):
    help = """This is the second step in linking albums and events, the first step is link_album_events_write
              To execute input the csv file through stdin.
    """

    def handle(self, *args, **options):
        events = Event.objects.all()
        albums = Album.objects.all()

        sys.stdin.readline()  # skip header
        rows = csv.reader(sys.stdin)
        for row in rows:
            if len(row) == 2 and row[0] != "" and row[1] != "":
                print("Linking " + row[0] + " and " + row[1])
                event_pk = row[0].split("-")[0]  # get pk from the cell
                album_pk = row[1].split("-")[0]

                event = events.get(pk=event_pk)
                album = albums.get(pk=album_pk)
                album.event = event
                album.save()

        print("Done linking")
