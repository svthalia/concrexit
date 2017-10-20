from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Exam = apps.get_model('education', 'Exam')

    for exam in Exam.objects.all():
        if exam.type == 'answers':
            exam.type = 'exam_answers'
            exam.save(update_fields=('type',))


def reverse_func(apps, schema_editor):
    Exam = apps.get_model('education', 'Exam')

    for exam in Exam.objects.all():
        if exam.type in ['exam_answers', 'partial_answers', 'resit_answers', 
                         'practice_answers']:
            exam.type = 'answers'
            exam.save(update_fields=('type',))


class Migration(migrations.Migration):
    
    dependencies = [
        # Without this dependency we get multiple leaf nodes
        ('education', '0006_auto_20171013_1535'),
        # The real dependency
        ('education', '0005_auto_20170906_2109'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
