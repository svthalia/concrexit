import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from activemembers.models import Board, Committee
from mailinglists.models import MailingList, VerbatimAddress
from members.models import Member


class Command(BaseCommand):
    help = "Migrates mailinglists. This should be done after migrating members"

    def handle(self, *args, **options):
        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured("MIGRATION_KEY not specified")
        url = "https://thalia.nu/api/export_mail.php?apikey={}&lists".format(
            settings.MIGRATION_KEY
        )
        lines = requests.get(url).text.split('\n')

        for lID in lines:
            if ':' in lID:
                raise Exception("Turns out we actually used aliasses.")
            if lID.isnumeric():
                url = ("https://thalia.nu/api/export_mail.php"
                       "?apikey={}&list={}".format(
                            settings.MIGRATION_KEY,
                            lID,
                        )
                       )
                lines = requests.get(url).text.split('\n')
                lines = lines[1:-2]
                name, prefix, arch, mod, *lines = lines
                mlist, cr = MailingList.objects.get_or_create(name=name)
                mlist.prefix = prefix
                mlist.archived = bool(arch)
                mlist.moderated = bool(mod)

                group_it = iter(lines[:lines.index('-')])
                groups = []
                while True:
                    try:
                        groups.append((next(group_it), []))
                        while True:
                            x = next(group_it)
                            if x == '=':
                                break
                            groups[-1][1].append(x)
                    except StopIteration:
                        break
                lines = lines[lines.index('-')+1:]
                users = lines[:lines.index('-')]
                verbatims = lines[lines.index('-')+1:]

                mlist.save()

                for user in users:
                    mlist.members.add(Member.objects.get(user__username=user))
                for g, users in groups:
                    try:
                        mlist.committees.add(Committee.objects.get(name_nl=g))
                    except Committee.DoesNotExist:
                        try:
                            mlist.committees.add(Board.objects.get(name_nl=g))
                        except Committee.DoesNotExist:
                            print("[{}] Did not find group '{}'".format(name,
                                                                        g))
                            print("    Adding individual users: {}".format(
                                ', '.join(users))
                            )
                            for user in users:
                                mlist.members.add(
                                    Member.objects.get(user__username=user))
                for v in verbatims:
                    obj = VerbatimAddress(address=v, mailinglist=mlist)
                    obj.save()

                mlist.save()
