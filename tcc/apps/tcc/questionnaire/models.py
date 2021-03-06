from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.utils.translation import ugettext_lazy as _
from .signals import update_score as update_score_signal


class EngagementMetric(models.Model):
    name = models.CharField(
        _('Metric name'),
        max_length=25,
        help_text=_('Short description of this engagement metric')
    )
    description = models.CharField(
        _('Metric description'),
        max_length=255,
        help_text=_('Briefly describe this engagement metric')
    )

    def __str__(self):
        return self.name


class QuestionnaireType(models.Model):
    description = models.CharField(max_length=35)

    def __str__(self):
        return self.description


class QuestionTemplate(models.Model):
    question = models.CharField(
        _('Question'),
        max_length=120
    )
    engagement_metric = models.ForeignKey(EngagementMetric, on_delete=models.CASCADE)

    def __str__(self):
        return self.question


class QuestionnaireTemplate(models.Model):
    description = models.CharField(
        _('Description'),
        max_length=80
    )
    questionnaire_type = models.ForeignKey(QuestionnaireType, on_delete=models.PROTECT)
    questions = models.ManyToManyField(QuestionTemplate)


class Questionnaire(models.Model):
    description = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text=_('A brief description for this questionnaire')
    )
    targets = models.ManyToManyField(settings.AUTH_USER_MODEL)
    questionnaire_type = models.ForeignKey(QuestionnaireType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False
    )
    is_staff = models.BooleanField(default=False)
    created_at = models.DateField(
        auto_now=True,
        editable=False
    )


class Answer(models.Model):
    value = models.PositiveIntegerField()
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    engagement_metric = models.ForeignKey(EngagementMetric, on_delete=models.PROTECT)


class Feedback(models.Model):
    text = models.TextField()
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)


def update_score(request, instance):
    score = instance.answer_set.aggregate(models.Avg('value'))['value__avg']
    Questionnaire.objects.filter(pk=instance.pk).update(score=score)
    instance.refresh_from_db()
    update_score_signal.send(sender=Questionnaire,
        instance=instance, request=request)
