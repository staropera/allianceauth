# Generated by Django 1.10.4 on 2016-12-14 10:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mumble', '0003_mumbleuser_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mumbleuser',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mumble', to=settings.AUTH_USER_MODEL),
        ),
    ]
