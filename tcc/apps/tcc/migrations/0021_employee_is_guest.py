# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-03-30 01:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tcc', '0020_employee_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='is_guest',
            field=models.BooleanField(default=False, verbose_name='Is a guest in the system?'),
        ),
    ]
