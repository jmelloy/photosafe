# Generated by Django 3.2.16 on 2022-11-22 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0006_auto_20210831_0313"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="photo",
            name="filename",
        ),
        migrations.AddField(
            model_name="photo",
            name="s3_original_path",
            field=models.TextField(blank=True, null=True),
        ),
    ]
