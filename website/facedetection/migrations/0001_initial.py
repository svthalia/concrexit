# Generated by Django 4.2 on 2023-05-02 11:22

from django.db import migrations, models
import django.db.models.deletion
import facedetection.models
import members.models.member
import secrets
import thumbnails.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("members", "0045_profile_receive_registration_confirmation"),
        ("photos", "0022_alter_like_member"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaceDetectionPhoto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("processing", "Processing"),
                            ("done", "Done"),
                            ("error", "Error"),
                        ],
                        default="processing",
                        help_text="Status of the encoding extraction process.",
                        max_length=16,
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        default=secrets.token_urlsafe,
                        editable=False,
                        help_text="Token used by a Lambda to authenticate to the API to submit encoding(s) for this source.",
                        max_length=40,
                    ),
                ),
                (
                    "photo",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="photos.photo"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PhotoFaceEncoding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("_field0", models.FloatField()),
                ("_field1", models.FloatField()),
                ("_field2", models.FloatField()),
                ("_field3", models.FloatField()),
                ("_field4", models.FloatField()),
                ("_field5", models.FloatField()),
                ("_field6", models.FloatField()),
                ("_field7", models.FloatField()),
                ("_field8", models.FloatField()),
                ("_field9", models.FloatField()),
                ("_field10", models.FloatField()),
                ("_field11", models.FloatField()),
                ("_field12", models.FloatField()),
                ("_field13", models.FloatField()),
                ("_field14", models.FloatField()),
                ("_field15", models.FloatField()),
                ("_field16", models.FloatField()),
                ("_field17", models.FloatField()),
                ("_field18", models.FloatField()),
                ("_field19", models.FloatField()),
                ("_field20", models.FloatField()),
                ("_field21", models.FloatField()),
                ("_field22", models.FloatField()),
                ("_field23", models.FloatField()),
                ("_field24", models.FloatField()),
                ("_field25", models.FloatField()),
                ("_field26", models.FloatField()),
                ("_field27", models.FloatField()),
                ("_field28", models.FloatField()),
                ("_field29", models.FloatField()),
                ("_field30", models.FloatField()),
                ("_field31", models.FloatField()),
                ("_field32", models.FloatField()),
                ("_field33", models.FloatField()),
                ("_field34", models.FloatField()),
                ("_field35", models.FloatField()),
                ("_field36", models.FloatField()),
                ("_field37", models.FloatField()),
                ("_field38", models.FloatField()),
                ("_field39", models.FloatField()),
                ("_field40", models.FloatField()),
                ("_field41", models.FloatField()),
                ("_field42", models.FloatField()),
                ("_field43", models.FloatField()),
                ("_field44", models.FloatField()),
                ("_field45", models.FloatField()),
                ("_field46", models.FloatField()),
                ("_field47", models.FloatField()),
                ("_field48", models.FloatField()),
                ("_field49", models.FloatField()),
                ("_field50", models.FloatField()),
                ("_field51", models.FloatField()),
                ("_field52", models.FloatField()),
                ("_field53", models.FloatField()),
                ("_field54", models.FloatField()),
                ("_field55", models.FloatField()),
                ("_field56", models.FloatField()),
                ("_field57", models.FloatField()),
                ("_field58", models.FloatField()),
                ("_field59", models.FloatField()),
                ("_field60", models.FloatField()),
                ("_field61", models.FloatField()),
                ("_field62", models.FloatField()),
                ("_field63", models.FloatField()),
                ("_field64", models.FloatField()),
                ("_field65", models.FloatField()),
                ("_field66", models.FloatField()),
                ("_field67", models.FloatField()),
                ("_field68", models.FloatField()),
                ("_field69", models.FloatField()),
                ("_field70", models.FloatField()),
                ("_field71", models.FloatField()),
                ("_field72", models.FloatField()),
                ("_field73", models.FloatField()),
                ("_field74", models.FloatField()),
                ("_field75", models.FloatField()),
                ("_field76", models.FloatField()),
                ("_field77", models.FloatField()),
                ("_field78", models.FloatField()),
                ("_field79", models.FloatField()),
                ("_field80", models.FloatField()),
                ("_field81", models.FloatField()),
                ("_field82", models.FloatField()),
                ("_field83", models.FloatField()),
                ("_field84", models.FloatField()),
                ("_field85", models.FloatField()),
                ("_field86", models.FloatField()),
                ("_field87", models.FloatField()),
                ("_field88", models.FloatField()),
                ("_field89", models.FloatField()),
                ("_field90", models.FloatField()),
                ("_field91", models.FloatField()),
                ("_field92", models.FloatField()),
                ("_field93", models.FloatField()),
                ("_field94", models.FloatField()),
                ("_field95", models.FloatField()),
                ("_field96", models.FloatField()),
                ("_field97", models.FloatField()),
                ("_field98", models.FloatField()),
                ("_field99", models.FloatField()),
                ("_field100", models.FloatField()),
                ("_field101", models.FloatField()),
                ("_field102", models.FloatField()),
                ("_field103", models.FloatField()),
                ("_field104", models.FloatField()),
                ("_field105", models.FloatField()),
                ("_field106", models.FloatField()),
                ("_field107", models.FloatField()),
                ("_field108", models.FloatField()),
                ("_field109", models.FloatField()),
                ("_field110", models.FloatField()),
                ("_field111", models.FloatField()),
                ("_field112", models.FloatField()),
                ("_field113", models.FloatField()),
                ("_field114", models.FloatField()),
                ("_field115", models.FloatField()),
                ("_field116", models.FloatField()),
                ("_field117", models.FloatField()),
                ("_field118", models.FloatField()),
                ("_field119", models.FloatField()),
                ("_field120", models.FloatField()),
                ("_field121", models.FloatField()),
                ("_field122", models.FloatField()),
                ("_field123", models.FloatField()),
                ("_field124", models.FloatField()),
                ("_field125", models.FloatField()),
                ("_field126", models.FloatField()),
                ("_field127", models.FloatField()),
                (
                    "photo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="encodings",
                        to="facedetection.facedetectionphoto",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ReferenceFace",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("processing", "Processing"),
                            ("done", "Done"),
                            ("error", "Error"),
                        ],
                        default="processing",
                        help_text="Status of the encoding extraction process.",
                        max_length=16,
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        default=secrets.token_urlsafe,
                        editable=False,
                        help_text="Token used by a Lambda to authenticate to the API to submit encoding(s) for this source.",
                        max_length=40,
                    ),
                ),
                (
                    "file",
                    thumbnails.fields.ImageField(
                        upload_to=facedetection.models.reference_face_uploadto
                    ),
                ),
                ("marked_for_deletion_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FaceDetectionUser",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("members.member",),
            managers=[
                ("objects", members.models.member.MemberManager()),
                ("current_members", members.models.member.CurrentMemberManager()),
                ("active_members", members.models.member.ActiveMemberManager()),
            ],
        ),
        migrations.CreateModel(
            name="ReferenceFaceEncoding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("_field0", models.FloatField()),
                ("_field1", models.FloatField()),
                ("_field2", models.FloatField()),
                ("_field3", models.FloatField()),
                ("_field4", models.FloatField()),
                ("_field5", models.FloatField()),
                ("_field6", models.FloatField()),
                ("_field7", models.FloatField()),
                ("_field8", models.FloatField()),
                ("_field9", models.FloatField()),
                ("_field10", models.FloatField()),
                ("_field11", models.FloatField()),
                ("_field12", models.FloatField()),
                ("_field13", models.FloatField()),
                ("_field14", models.FloatField()),
                ("_field15", models.FloatField()),
                ("_field16", models.FloatField()),
                ("_field17", models.FloatField()),
                ("_field18", models.FloatField()),
                ("_field19", models.FloatField()),
                ("_field20", models.FloatField()),
                ("_field21", models.FloatField()),
                ("_field22", models.FloatField()),
                ("_field23", models.FloatField()),
                ("_field24", models.FloatField()),
                ("_field25", models.FloatField()),
                ("_field26", models.FloatField()),
                ("_field27", models.FloatField()),
                ("_field28", models.FloatField()),
                ("_field29", models.FloatField()),
                ("_field30", models.FloatField()),
                ("_field31", models.FloatField()),
                ("_field32", models.FloatField()),
                ("_field33", models.FloatField()),
                ("_field34", models.FloatField()),
                ("_field35", models.FloatField()),
                ("_field36", models.FloatField()),
                ("_field37", models.FloatField()),
                ("_field38", models.FloatField()),
                ("_field39", models.FloatField()),
                ("_field40", models.FloatField()),
                ("_field41", models.FloatField()),
                ("_field42", models.FloatField()),
                ("_field43", models.FloatField()),
                ("_field44", models.FloatField()),
                ("_field45", models.FloatField()),
                ("_field46", models.FloatField()),
                ("_field47", models.FloatField()),
                ("_field48", models.FloatField()),
                ("_field49", models.FloatField()),
                ("_field50", models.FloatField()),
                ("_field51", models.FloatField()),
                ("_field52", models.FloatField()),
                ("_field53", models.FloatField()),
                ("_field54", models.FloatField()),
                ("_field55", models.FloatField()),
                ("_field56", models.FloatField()),
                ("_field57", models.FloatField()),
                ("_field58", models.FloatField()),
                ("_field59", models.FloatField()),
                ("_field60", models.FloatField()),
                ("_field61", models.FloatField()),
                ("_field62", models.FloatField()),
                ("_field63", models.FloatField()),
                ("_field64", models.FloatField()),
                ("_field65", models.FloatField()),
                ("_field66", models.FloatField()),
                ("_field67", models.FloatField()),
                ("_field68", models.FloatField()),
                ("_field69", models.FloatField()),
                ("_field70", models.FloatField()),
                ("_field71", models.FloatField()),
                ("_field72", models.FloatField()),
                ("_field73", models.FloatField()),
                ("_field74", models.FloatField()),
                ("_field75", models.FloatField()),
                ("_field76", models.FloatField()),
                ("_field77", models.FloatField()),
                ("_field78", models.FloatField()),
                ("_field79", models.FloatField()),
                ("_field80", models.FloatField()),
                ("_field81", models.FloatField()),
                ("_field82", models.FloatField()),
                ("_field83", models.FloatField()),
                ("_field84", models.FloatField()),
                ("_field85", models.FloatField()),
                ("_field86", models.FloatField()),
                ("_field87", models.FloatField()),
                ("_field88", models.FloatField()),
                ("_field89", models.FloatField()),
                ("_field90", models.FloatField()),
                ("_field91", models.FloatField()),
                ("_field92", models.FloatField()),
                ("_field93", models.FloatField()),
                ("_field94", models.FloatField()),
                ("_field95", models.FloatField()),
                ("_field96", models.FloatField()),
                ("_field97", models.FloatField()),
                ("_field98", models.FloatField()),
                ("_field99", models.FloatField()),
                ("_field100", models.FloatField()),
                ("_field101", models.FloatField()),
                ("_field102", models.FloatField()),
                ("_field103", models.FloatField()),
                ("_field104", models.FloatField()),
                ("_field105", models.FloatField()),
                ("_field106", models.FloatField()),
                ("_field107", models.FloatField()),
                ("_field108", models.FloatField()),
                ("_field109", models.FloatField()),
                ("_field110", models.FloatField()),
                ("_field111", models.FloatField()),
                ("_field112", models.FloatField()),
                ("_field113", models.FloatField()),
                ("_field114", models.FloatField()),
                ("_field115", models.FloatField()),
                ("_field116", models.FloatField()),
                ("_field117", models.FloatField()),
                ("_field118", models.FloatField()),
                ("_field119", models.FloatField()),
                ("_field120", models.FloatField()),
                ("_field121", models.FloatField()),
                ("_field122", models.FloatField()),
                ("_field123", models.FloatField()),
                ("_field124", models.FloatField()),
                ("_field125", models.FloatField()),
                ("_field126", models.FloatField()),
                ("_field127", models.FloatField()),
                (
                    "matches",
                    models.ManyToManyField(
                        editable=False,
                        related_name="matches",
                        to="facedetection.photofaceencoding",
                    ),
                ),
                (
                    "reference",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="facedetection.referenceface",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="referenceface",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reference_faces",
                to="facedetection.facedetectionuser",
            ),
        ),
    ]
