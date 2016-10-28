# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-28 00:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0002_questionnaire_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=80, verbose_name='Description')),
                ('questionnaire_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='questionnaire.QuestionnaireType')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=120, verbose_name='Question')),
                ('engagement_metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaire.EngagementMetric')),
            ],
        ),
        migrations.AddField(
            model_name='questionnairetemplate',
            name='questions',
            field=models.ManyToManyField(to='questionnaire.QuestionTemplate'),
        ),
    ]
