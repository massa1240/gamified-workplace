from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import LANGUAGE_SESSION_KEY, ugettext_lazy as _
from django.utils.functional import cached_property
from .questionnaire.models import EngagementMetric, Questionnaire
from .managers import ProductManager, EmployeeManager, TeamManager, GoalManager
from datetime import datetime, timedelta


MANAGER_COLLABORATOR = 1
COLLABORATOR_SATISFACTION = 2
TASK_FEEDBACK = 3


class Department(models.Model):

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    name = models.CharField(
        max_length=25
    )

    def __str__(self):
        return self.name


class Occupation(models.Model):

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')

    name = models.CharField(
        max_length=25
    )

    def __str__(self):
        return self.name


def images_path(instance, filename):
    extension = filename.split(".")[-1]
    return '{0}/{1}.{2}'.format(
        instance._meta.verbose_name_plural,
        instance.id,
        extension
    )


class Product(models.Model):

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    objects = ProductManager()
    name = models.CharField(
        _('Product name'),
        max_length=45
    )
    price = models.PositiveIntegerField(
        _('Price'),
        help_text=_('Cost in points')
    )
    stock = models.IntegerField(
        _('Stock'),
        default=-1,
        help_text=_('-1 means unlimited stock')
    )
    max_per_user = models.PositiveIntegerField(
        _('Max purchases per user'),
        default=0,
        help_text=_('0 means no limit')
    )
    is_active = models.BooleanField(
        default=True
    )
    is_featured = models.BooleanField()
    photo = models.ImageField(
        null=True,
        blank=False,
        upload_to=images_path
    )

    def relevant_stock(self):
        if self.max_per_user > 0:
            return self.max_per_user
        elif self.stock > -1:
            return self.stock
        else:
            return -1

    def __str__(self):
        return self.name


GOAL_LEVELS = (
    (4, _('Platinum')),
    (3, _('Gold')),
    (2, _('Silver')),
    (1, _('Bronze'))
)

ONCE = 1
DAILY = 2
WEEKLY = 3
MONTHLY = 4

GOAL_FREQUENCIES = (
    (ONCE, _('Once')),
    (DAILY, _('Daily')),
    (WEEKLY, _('Weekly')),
    (MONTHLY, _('Monthly'))
)


class Goal(models.Model):

    class Meta:
        verbose_name = _('Goal')
        verbose_name_plural = _('Goals')

    objects = GoalManager()

    description = models.CharField(
        max_length=40,
        help_text=_('A short name to describe the goal')
    )
    money = models.PositiveIntegerField(
        _('Diamonds'),
        default=0,
        help_text=_('Diamonds received when employee finishes this goal')
    )
    frequency = models.PositiveIntegerField(
        choices=GOAL_FREQUENCIES,
        default=1,
        help_text=_('Frequency rate this goal happens'),
    )
    starts_at = models.DateField(
        _('Starts on'),
    )
    ends_at = models.DateField(
        _('Ends on'),
    )
    level = models.PositiveIntegerField(
        choices=GOAL_LEVELS,
        default=1,
        help_text=_('The level of importance of this goal'),
    )
    is_active = models.BooleanField(
        default=True
    )
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.description


def user_directory_path(instance, filename):
    extension = filename.split(".")[-1]
    return 'avatar/{0}.{1}'.format(instance.user.id, extension)


class Employee(models.Model):

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')

    objects = EmployeeManager()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    occupation = models.ForeignKey(Occupation, on_delete=models.PROTECT, null=True)
    nickname = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )
    hiring_date = models.DateField(
        null=True,
        blank=False,
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    first_login = models.BooleanField(
        _('Is his first login?'),
        default=True,
        editable=False,
        help_text=_('Identify first login user.')
    )
    money = models.PositiveIntegerField(
        editable=False,
        default=0
    )
    energy = models.PositiveIntegerField(
        editable=False,
        default=3
    )
    last_energy_update = models.DateField(
        null=False,
        blank=False,
        editable=False,
    )
    inventory = models.ManyToManyField(Product, through='Purchase')
    badges = models.ManyToManyField(Goal, through='Badge')
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to=user_directory_path
    )
    language = models.CharField(
        _('Language'),
        max_length=5,
        default='pt-br',
        choices=settings.LANGUAGES
    )
    is_guest = models.BooleanField(
        _('Is a guest in the system?'),
        default=False,
    )

    def reset_energy(self):
        now = datetime.now()
        if now.isocalendar()[1] > self.last_energy_update.isocalendar()[1]:
            self.last_energy_update = now
            self.energy = 3
            self.save()
            return self.energy
        return False

    def get_inventory(self):
        return self.inventory \
            .annotate(
                items_left=models.Count('purchase__id') - models.Sum(
                    models.Case(
                        models.When(
                            purchase__used_at__isnull=False,
                            then=1
                        ),
                        models.When(
                            purchase__used_at__isnull=True,
                            then=0
                        ),
                        output_field=models.IntegerField()
                    )
                )
            )

    def __str__(self):
        return self.nickname or self.user.get_short_name() or self.user.username

    @cached_property
    def points(self):
        points_calc = models.Sum('answer__value')
        points = self.user.questionnaire_set \
            .exclude(questionnaire_type__in=[COLLABORATOR_SATISFACTION]) \
            .aggregate(points=points_calc)['points'] or 0
        return int(points/10)

    def answered_satisfaction_questionnaire(self):
        last_week = datetime.today() + timedelta(days=-7)
        return self.user.questionnaire_set \
            .filter(questionnaire_type=COLLABORATOR_SATISFACTION, created_at__gte=last_week) \
            .exists()

    def missing_team_questionnaire(self):
        last_week = datetime.today() + timedelta(days=-7)
        return self.team_set.filter(models.Q(
            teamquestionnairecontrol__created_at__lt=last_week
        ) | models.Q(teamquestionnairecontrol=None), ended_at=None)

    def missing_team_final_questionnaire(self):
        return self.team_set.filter(teamquestionnairecontrol=None).exclude(ended_at=None)

    @property
    def feedbacks(self):
        return self.user.questionnaire_set \
            .exclude(questionnaire_type__in=[COLLABORATOR_SATISFACTION]) \
            .count()

    @cached_property
    def overall_skill_bar(self):
        skill_calc = models.Avg('answer__value')
        return self.user.questionnaire_set.aggregate(skill_bar=skill_calc)['skill_bar'] or 0


class Badge(models.Model):

    class Meta:
        verbose_name = _('Badge')
        verbose_name_plural = _('Badges')

    goal = models.ForeignKey(Goal, on_delete=models.PROTECT)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    received_at = models.DateField(
        null=False,
        blank=False
    )
    level = models.PositiveIntegerField(
        choices=GOAL_LEVELS,
        null=False,
        blank=False,
        editable=False,
        help_text=_('The level of importance of this goal'),
    )

    def __str__(self):
        return _('%(employee_name)s\'s %(badge_name)s badge') % {
            'employee_name': self.employee,
            'badge_name': self.goal
        }

    def clean(self):
        if self.level is None:
            self.level = self.goal.level


class Purchase(models.Model):

    class Meta:
        verbose_name = _('Purchase')
        verbose_name_plural = _('Purchases')

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    cost = models.PositiveIntegerField(
        editable=False,
        null=False,
        blank=True,
    )
    used_at = models.DateField(
        null=True,
        blank=True,
        editable=False
    )
    purchase_date = models.DateField(
        auto_now=True,
        editable=False
    )

    def clean(self):
        if self.employee.money < self.product.price:
            raise ValidationError(_('You don\'t have enough money.'))

        if self.product.stock == 0 or not self.product.is_active:
            raise ValidationError(_('This item is not available.'))

        count_product = self.employee.inventory.filter(id=self.product.id).count()
        if self.product.max_per_user > 0 and count_product >= self.product.max_per_user:
            raise ValidationError(_('You already own this product.'))

        if self.cost is None:
            self.cost = self.product.price


class Team(models.Model):

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')

    objects = TeamManager()
    name = models.CharField(
        max_length=25
    )
    members = models.ManyToManyField(Employee)
    created_at = models.DateField()
    ended_at = models.DateField(
        null=True,
        blank=True
    )
    photo = models.ImageField(
        null=True,
        blank=False,
        upload_to=images_path
    )

    def is_active(self):
        return self.ended_at == None

    def __str__(self):
        return self.name

    @cached_property
    def points(self):
        points_calc = models.Sum('questionnaire__answer__value')
        points = self.teamquestionnaire_set \
            .exclude(questionnaire__questionnaire_type__in=[COLLABORATOR_SATISFACTION]) \
            .aggregate(points=points_calc)['points'] or 0
        return int(points/10)

    def missing_questionnaire(self, employee):
        if self.is_active():
            return employee.missing_team_questionnaire().filter(id=self.pk).exists()
        else:
            return employee.missing_team_final_questionnaire().filter(id=self.pk).exists()


class TeamQuestionnaire(models.Model):

    class Meta:
        verbose_name = _('Team questionnaire')
        verbose_name_plural = _('Team questionnaires')

    questionnaire = models.OneToOneField(
        Questionnaire,
        on_delete=models.CASCADE,
        primary_key=True
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )


class TeamQuestionnaireControl(models.Model):

    class Meta:
        verbose_name = _('Team questionnaire control')
        verbose_name_plural = _('Team questionnaire controls')

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now=True)


class EngagementMetricConfig(models.Model):

    class Meta:
        verbose_name = _('Engagement metric config')
        verbose_name_plural = _('Engagement metric configs')

    engagement_metric = models.OneToOneField(
        EngagementMetric,
        on_delete=models.CASCADE,
        primary_key=True
    )
    icon_class = models.CharField(
        _('Icon class'),
        max_length=25,
        help_text=_('An icon class (eg: fontawesome) to be displayed.')
    )
    is_staff = models.BooleanField(
        _('Displayed only for staff'),
        default=False,
        help_text=_('Should this metric be displayed only by staff?')
    )


class LoginCount(models.Model):

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateField(
        auto_now=True,
        editable=False
    )

    def __str__(self):
        return self.employee.__str__()


@receiver(post_save, sender=Purchase)
def update_data_after_purchase(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        if product.stock > 0:
            product.stock -= 1
            product.save()

        employee = instance.employee
        employee.money -= instance.cost
        employee.save()


@receiver(post_save, sender=Badge)
def update_data_after_earning_badge(sender, instance, created, **kwargs):
    if created:
        goal = instance.goal
        employee = instance.employee

        Employee.objects.add_money_to_user(employee.user, goal.money)


@receiver(post_save, sender=TeamQuestionnaire)
def update_targets(sender, instance, created, **kwargs):
    if created:
        users = []
        for member in instance.team.members.all():
            users.append(member.user)
        instance.questionnaire.targets = users
        instance.questionnaire.save()


@receiver(user_logged_in)
def set_lang(sender, **kwargs):
    lang_code = kwargs['user'].employee.language
    kwargs['request'].session[LANGUAGE_SESSION_KEY] = lang_code


@receiver(user_logged_in)
def update_user_login(sender, user, **kwargs):
    if user.is_staff:
        return

    user.employee.logincount_set.create()
    user.save()
