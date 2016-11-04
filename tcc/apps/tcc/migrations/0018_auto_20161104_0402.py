# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-04 04:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tcc', '0017_teamquestionnairecontrol'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='energy',
            field=models.PositiveIntegerField(default=3, editable=False),
        ),
        migrations.AddField(
            model_name='employee',
            name='last_energy_update',
            field=models.DateField(default=django.utils.timezone.now, editable=False),
            preserve_default=False,
        ),
    ]
