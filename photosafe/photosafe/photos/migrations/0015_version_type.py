# Generated by Django 3.2.19 on 2023-07-02 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0014_photo_library'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='type',
            field=models.TextField(blank=True, null=True),
        ),
    ]