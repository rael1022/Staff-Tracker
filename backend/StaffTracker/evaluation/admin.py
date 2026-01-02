from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Evaluation

User = get_user_model()

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'training_title_truncated',
        'user_info',
        'rating_display',
        'recommendation_status',
        'evaluation_date_formatted',
        'user_role'
    ]
    
    list_filter = [
        'rating',
        'question5_would_recommend',
        'evaluation_date',
        'training__date',
        'training__trainer',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'training__training_title',
        'feedback'
    ]
    
    readonly_fields = ['evaluation_date']
    
    fieldsets = (
        ('Base Information', {
            'fields': ('training', 'user', 'evaluation_date')
        }),
        ('Assessment content', {
            'fields': (
                'rating',
                'question1_rating',
                'question2_rating',
                'question3_rating',
                'question4_rating',
                'question5_would_recommend'
            )
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
    )
    
    def training_title_truncated(self, obj):
        title = obj.training.training_title
        return title[:50] + '...' if len(title) > 50 else title
    training_title_truncated.short_description = 'Training'
    
    def user_info(self, obj):
        return f"{obj.user.username} ({obj.user.get_full_name() or 'No name'})"
    user_info.short_description = 'User'
    
    def rating_display(self, obj):
        return f"{obj.rating}/5"
    rating_display.short_description = 'Rating'
    
    def recommendation_status(self, obj):
        return '✓' if obj.question5_would_recommend else '✗'
    recommendation_status.short_description = 'Recommends'
    
    def evaluation_date_formatted(self, obj):
        return obj.evaluation_date.strftime('%Y-%m-%d %H:%M')
    evaluation_date_formatted.short_description = 'Submitted'
    
    def user_role(self, obj):
        if hasattr(obj.user, 'userprofile'):
            return obj.user.userprofile.role
        return 'N/A'