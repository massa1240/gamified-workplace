from django.contrib import messages
from .models import (
    Employee,
    MANAGER_COLLABORATOR,
    COLLABORATOR_SATISFACTION,
    TASK_FEEDBACK
)


def update_money(sender, instance, request, **kwargs):
    if request.user.employee.is_guest:
        return

    money = 0
    added_money = 0
    users = []
    if instance.questionnaire_type_id is MANAGER_COLLABORATOR or \
        instance.questionnaire_type_id is TASK_FEEDBACK:

        money = int(instance.score)
        users = instance.targets.values_list('id', flat=True)
        if request.user.is_staff:
            money += 10
        else:
            added_money = 10
            Employee.objects.add_money_to_user(request.user, added_money)

    elif instance.questionnaire_type_id is COLLABORATOR_SATISFACTION:
        added_money = money = 10
        users = [request.user.pk]

    if not request.user.is_staff and instance.questionnaire_type_id is TASK_FEEDBACK:
        messages.add_message(
            request,
            messages.WARNING,
            "<strong><i class=\"fa fa-bolt\"></i> - 1"
        )
        Employee.objects.decrease_energy(request.user)

    if added_money is not 0:
        messages.add_message(
            request,
            messages.INFO,
            "<strong><i class=\"fa fa-diamond\"></i> + D$ %d.</strong>" % (added_money)
        )

    Employee.objects.add_money_to_users(users, money)
