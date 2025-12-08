# Manual migration for upload fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0017_alter_version_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='filename',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='file_path',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='content_type',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='file_size',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
