import json
import os

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date
from django.utils.translation import activate

from education.models import Category, Course, Exam, Summary
from utils.management.commands import legacylogin


def filefield_from_url(filefield, url):
    file = ContentFile(requests.get(url).content)
    filefield.save(os.path.basename(url), file)


class Command(legacylogin.Command):
    help = 'Scrapes the education data from the old Thalia website'

    def handle(self, *args, **options):
        activate('en')

        if not settings.MIGRATION_KEY:
            raise ImproperlyConfigured("MIGRATION_KEY not specified")
        url = "https://thalia.nu/index.php/onderwijs/api?apikey={}".format(
            settings.MIGRATION_KEY
        )

        input_val = input(
            'Do you want to delete all existing objects? (type yes or no) ')
        if input_val == 'yes':
            Summary.objects.all().delete()
            Exam.objects.all().delete()
            Course.objects.all().delete()
            Category.objects.all().delete()

        session = requests.Session()
        src = session.get(url).text

        if 'invalid api key' in src:
            raise PermissionDenied('Invalid API key')

        data = json.loads(src)

        category_map = {}

        print('Importing categories')
        for key in data['categories']:
            name = data['categories'][key]
            id = Category()
            id.name_nl = name
            id.name_en = name
            id.save()
            category_map[key] = id.pk
        print('Importing categories complete')

        course_map = {}

        print('Importing courses')
        for key in data['courses']:
            src = data['courses'][key]
            course = Course()
            course.name_nl = src['name']
            course.name_en = src['name']
            course.course_code = src['course_code']
            course.shorthand_nl = src['course_shorthand']
            course.shorthand_en = src['course_shorthand']
            course.ec = int(src['e_c_t_s'])
            course.period = src['quarter'].replace(' en ', ' & ')
            course.since = src['since']
            course.until = src['until'] if src['until'] != 0 else None
            course.save()

            for id in src['categories']:
                course.categories.add(Category.objects
                                      .get(pk=category_map[str(id)]))

            course_map[key] = course.pk

        print('Combining courses with predecessors')
        for key in data['courses']:
            src = data['courses'][key]
            course = Course.objects.get(pk=course_map[key])
            try:
                for id in src['predecessors']:
                    if id == 0:
                        continue
                    old_course = Course.objects.get(pk=course_map[str(id)])
                    course.old_courses.add(old_course)
            except KeyError:
                pass
            course.save()
        print('Importing courses complete')

        print('Importing summaries')
        for key in data['summaries']:
            src = data['summaries'][key]
            summary = Summary()
            summary.name = src['name']
            summary.author = '' if src['author'] is None else src['author']
            summary.year = int(src['year'])
            summary.uploader_date = parse_date(src['uploader_date'])
            summary.accepted = src['accepted'] == '1'
            course_id = str(src['course_id'])
            summary.course = Course.objects.get(pk=course_map[course_id])

            try:
                summary.uploader = User.objects.get(username=src['uploader'])
            except User.DoesNotExist:
                summary.uploader = User.objects.get(pk=1)

            filefield_from_url(summary.file, src['file_url'])
            summary.save()
        print('Importing summaries complete')

        print('Importing exams')
        for key in data['exams']:
            src = data['exams'][key]
            exam = Exam()
            exam.name = '' if src['name'] is None else src['name']
            exam.accepted = src['accepted'] == '1'
            course_id = str(src['course_id'])
            exam.course = Course.objects.get(pk=course_map[course_id])
            type_map = {
                0: 'document',
                1: 'exam',
                2: 'partial',
                3: 'resit',
                5: 'practice'
            }
            exam.type = type_map.get(int(src['type']), 'document')
            exam.exam_date = parse_date(src['date'])
            exam.uploader_date = parse_date(src['uploader_date'])

            try:
                exam.uploader = User.objects.get(username=src['uploader'])
            except User.DoesNotExist:
                exam.uploader = User.objects.get(pk=1)

            filefield_from_url(exam.file, src['file_url'])
            exam.save()
        print('Importing exams complete')
