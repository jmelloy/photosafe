# Generated by Django 3.2.16 on 2022-11-26 00:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0008_photo_s3_live_path"),
    ]

    operations = [
        migrations.CreateModel(
            name="Version",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("version", models.TextField()),
                ("s3_path", models.TextField()),
                (
                    "photo_uuid",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="photos.photo"
                    ),
                ),
            ],
        ),
    ]
