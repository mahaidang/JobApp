# Generated by Django 5.1.6 on 2025-05-28 15:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0009_verificationrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='jobs.job')),
            ],
        ),
    ]
