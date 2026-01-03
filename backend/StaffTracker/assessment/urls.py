from django.urls import path
from . import views

urlpatterns = [
    # Trainer
    path('trainer/manage-questions/', views.manage_assessment_questions, name='manage_assessment_questions'),
    path('trainer/manage-questions/<int:training_id>/', views.manage_assessment_questions, name='manage_assessment_questions_training'),
    path('trainer/view-results/', views.view_results, name='view_results'),
    path('trainer/view-results/<int:training_id>/', views.view_results, name='view_results_training'),
    
    # Employee
    path('pre/<int:training_id>/', views.create_pre_assessment, name='pre_assessment'),
    path('post/<int:training_id>/', views.create_post_assessment, name='post_assessment'),
    path('my-results/', views.employee_results, name='employee_results'),
]