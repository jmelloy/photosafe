# Generated by Django 3.1.8 on 2021-08-31 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("photos", "0005_photo_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="masterFingerprint",
            field=models.TextField(null=True),
        ),
    ]