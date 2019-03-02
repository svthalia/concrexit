from django.core.management.base import BaseCommand

from members import services


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run instead of saving data',
        )

    def handle(self, *args, **options):
        processed = services.execute_data_minimisation(options['dry-run'])
        for p in processed:
            print('Removed data for {}'.format(p))
