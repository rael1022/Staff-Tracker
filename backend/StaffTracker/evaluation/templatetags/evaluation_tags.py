from django import template
from ..models import Evaluation

register = template.Library()

@register.filter
def has_evaluated(training, user):
    if not user or not user.is_authenticated:
        return False
    return Evaluation.objects.filter(training=training, user=user).exists()

@register.filter
def get_user_evaluation(training, user):
    if not user or not user.is_authenticated:
        return None
    try:
        return Evaluation.objects.get(training=training, user=user)
    except Evaluation.DoesNotExist:
        return None

@register.filter
def can_evaluate_training(training, user):
    from django.apps import apps
    
    if not user or not user.is_authenticated:
        return False, "User not logged in"
    
    if Evaluation.objects.filter(user=user, training=training).exists():
        return False, "Already evaluated"
    
    try:
        Registration = apps.get_model('training', 'TrainingRegistration')
    except LookupError:
        return False, "Registration module unavailable"
    
    try:
        registration = Registration.objects.get(
            training=training,
            employee=user
        )
        
        if registration.status != 'Approved':
            return False, f"Registration not approved ({registration.status})"
        
        if registration.complete_status != 'Completed':
            return False, f"Training not completed ({registration.complete_status})"
        
    except Registration.DoesNotExist:
        return False, "This training was not registered for."
    
    return True, "Can be evaluated"