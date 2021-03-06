# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-24 17:48
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='EngagementMetric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Short description of this engagement metric', max_length=25, verbose_name='Metric name')),
                ('description', models.CharField(help_text='Briefly describe this engagement metric', max_length=255, verbose_name='Metric description')),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=3, null=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('created_at', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionnaireType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=35)),
            ],
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='questionnaire_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='questionnaire.QuestionnaireType'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='targets',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='feedback',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaire.Questionnaire'),
        ),
        migrations.AddField(
            model_name='answer',
            name='engagement_metric',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='questionnaire.EngagementMetric'),
        ),
        migrations.AddField(
            model_name='answer',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaire.Questionnaire'),
        ),
    ]
