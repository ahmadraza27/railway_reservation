# Generated by Django 5.1.4 on 2024-12-06 19:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0006_cabin_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='route',
            name='location',
        ),
    ]
