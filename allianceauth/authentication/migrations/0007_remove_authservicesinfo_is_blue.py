# Generated by Django 1.10.1 on 2016-09-10 21:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_auto_20160910_0542'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authservicesinfo',
            name='is_blue',
        ),
    ]
