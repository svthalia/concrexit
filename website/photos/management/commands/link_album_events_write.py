import csv
import sys

from django.core.management.base import BaseCommand

from events.models import Event
from photos.models import Album


def write(events, albums, output):
    for j in range(max(len(events), len(albums))):
        if j < len(events):
            event = (
                str(events[j].pk)
                + "-"
                + events[j].title
                + "-"
                + str(events[j].start.date())
            )
        else:
            event = ""
        if j < len(albums):
            album = (
                str(albums[j].pk) + "-" + albums[j].title + "-" + str(albums[j].date)
            )
        else:
            album = ""
        output.writerow([event, album])


class Command(BaseCommand):
    help = """This is the first step in linking albums and events, the second step is link_album_events_read
        How to use this script:
        Send this output to a csv file.
        Edit this csv file such that albums and events that should be linked are next to each other
        If an album is next to an empty cell, it will not be linked
        Don't change a cells' contents itself
        When you are done, input the file into the command link_album_events_read"""

    def handle(self, *args, **options):
        events = Event.objects.order_by("start").all()
        albums = Album.objects.order_by("date").filter(event__isnull=True)

        # partition the events and albums by date
        partitioned_events = [[events[0]]]
        last_date = events[0].start.date()
        for e in events[1:]:
            if e.start.date() == last_date:
                partitioned_events[len(partitioned_events) - 1].append(e)
            else:
                partitioned_events.append([e])
                last_date = e.start.date()

        partitioned_albums = [[albums[0]]]
        last_date = albums[0].date
        for a in albums[1:]:
            if a.date == last_date:
                partitioned_albums[len(partitioned_albums) - 1].append(a)
            else:
                partitioned_albums.append([a])
                last_date = a.date

        i = 0  # index of partitioned_events
        j = 0  # index of partitioned_albums
        output = csv.writer(sys.stdout)
        output.writerow(["Event (id-title-startdate)", "Album (id-title-date)"])
        while i < len(partitioned_events) or j < len(partitioned_albums):
            if i == len(partitioned_events):
                # no events left, write albums
                write([], partitioned_albums[j], output)
            elif j == len(partitioned_albums):
                # no albums left, write events
                write(partitioned_events[i], [], output)
                i += 1
            elif partitioned_albums[j][0].date < partitioned_events[i][0].start.date():
                # write albums
                write([], partitioned_albums[j], output)
                j += 1
            elif partitioned_albums[j][0].date > partitioned_events[i][0].start.date():
                # write events
                write(partitioned_events[i], [], output)
                i += 1
            elif partitioned_albums[j][0].date == partitioned_events[i][0].start.date():
                # events and albums on the same day, write both
                write(partitioned_events[i], partitioned_albums[j], output)
                i += 1
                j += 1
