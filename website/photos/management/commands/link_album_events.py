from django.core.management.base import BaseCommand

from events.models import Event
from photos.models import Album

import csv


def write(events, albums, file):
    for j in range(max(len(events), len(albums))):
        if j < len(events):
            file.write(
                str(events[j].pk)
                + "-"
                + events[j].title
                + "-"
                + str(events[j].start.date())
            )
        file.write(",")
        if j < len(albums):
            file.write(
                str(albums[j].pk) + "-" + albums[j].title + "-" + str(albums[j].date)
            )
        file.write("\n")


class Command(BaseCommand):
    def handle(self, *args, **options):
        events = Event.objects.order_by("start").all()
        albums = Album.objects.order_by("date").all()

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

        print("Writing to link_album_events.csv")
        i = 0  # index of partitioned_events
        j = 0  # index of partitioned_albums
        f = open("link_album_events.csv", "w")
        writer = csv.writer(f)
        writer.writerow["Event (id-title-startdate)", "Album (id-title-date)\n"]
        while i < len(partitioned_events) or j < len(partitioned_albums):
            if i == len(partitioned_events):
                # no events left, write albums
                write([], partitioned_albums[j], writer)
            elif j == len(partitioned_albums):
                # no albums left, write events
                write(partitioned_events[i], [], writer)
                i += 1
            elif partitioned_albums[j][0].date < partitioned_events[i][0].start.date():
                # write albums
                write([], partitioned_albums[j], writer)
                j += 1
            elif partitioned_albums[j][0].date > partitioned_events[i][0].start.date():
                # write events
                write(partitioned_events[i], [], writer)
                i += 1
            elif partitioned_albums[j][0].date == partitioned_events[i][0].start.date():
                # events and albums on the same day, write both
                write(partitioned_events[i], partitioned_albums[j], f)
                i += 1
                j += 1
        f.close()

        print("done")
        print(
            "Please edit the file such that albums and events that should be linked are next to eachother"
        )
        print("If an album or an event is next to an empty cell, it will not be linked")
        print("Don't change cell's content")
        print("When you are done, press enter and the same file will be read again.")

        while True:
            input()
            try:
                f = open("link_album_events.csv", "r")
            except FileNotFoundError:
                print("link_album_events.csv not found")
            else:
                break

        f.readline()  # skip header
        rows = csv.reader(f)
        for row in rows:
            print(row)
            if len(row) == 2 and row[0] != "" and row[1] != "":
                print("Linking " + row[0] + " and " + row[1])
                event_pk = row[0].split("-")[0]  # get pk from the cell
                album_pk = row[1].split("-")[0]

                event = events.get(pk=event_pk)
                album = albums.get(pk=album_pk)
                album.event = event
                album.save()

        print("Done linking")
