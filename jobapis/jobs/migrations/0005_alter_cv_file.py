# Generated by Django 5.1.6 on 2025-05-06 08:31

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_alter_cv_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cv',
            name='file',
            field=cloudinary.models.CloudinaryField(max_length=255),
        ),
    ]
