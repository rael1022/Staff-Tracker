from django.contrib import admin
from .models import AssessmentQuestion, PreAssessment, PostAssessment

@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'training', 'question_type', 'question_text_short', 'correct_answer', 'marks']
    list_filter = ['question_type', 'training']
    search_fields = ['question_text', 'training__title']
    list_editable = ['marks']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'

@admin.register(PreAssessment)
class PreAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'training', 'assessment_date', 'score', 'stress_level', 'status']
    list_filter = ['status', 'training']
    search_fields = ['user__username', 'training__title']
    readonly_fields = ['score', 'assessment_date']

@admin.register(PostAssessment)
class PostAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'training', 'assessment_date', 'score', 'status']
    list_filter = ['status', 'training']
    search_fields = ['user__username', 'training__title']
    readonly_fields = ['score', 'assessment_date']