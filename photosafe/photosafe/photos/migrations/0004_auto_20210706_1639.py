# Generated by Django 3.1.8 on 2021-07-06 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0003_photo_s3_edited_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='masterFingerprint',
            field=models.TextField(),
        ),
    ]