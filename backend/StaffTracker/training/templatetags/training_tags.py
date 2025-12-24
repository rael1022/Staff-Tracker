from django import template
from training.models import TrainingRegistration

register = template.Library()

@register.filter
def get_training_registration(registrations, training_id):
    return registrations.filter(training_id=training_id).first()
