from django import template
from assessment.models import AssessmentQuestion, PreAssessment, PostAssessment

register = template.Library()

@register.filter
def has_pre_assessment_questions(training_id):
    return AssessmentQuestion.objects.filter(
        training_id=training_id,
        question_type='pre'
    ).exists()

@register.filter
def has_post_assessment_questions(training_id):
    return AssessmentQuestion.objects.filter(
        training_id=training_id,
        question_type='post'
    ).exists()

@register.filter
def has_completed_pre_assessment(training_id, user):
    if not user.is_authenticated:
        return False
    return PreAssessment.objects.filter(
        training_id=training_id,
        user=user,
        status='Completed'
    ).exists()

@register.filter
def has_completed_post_assessment(training_id, user):
    if not user.is_authenticated:
        return False
    return PostAssessment.objects.filter(
        training_id=training_id,
        user=user,
        status='Completed'
    ).exists()