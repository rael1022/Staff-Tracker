from django.urls import path
from . import views

urlpatterns = [
    path('pre/<int:training_id>/', views.create_pre_assessment, name='pre_assessment'),
    path('post/<int:training_id>/', views.create_post_assessment, name='post_assessment'),
    path('api/questions/<int:training_id>/<str:question_type>/', 
         views.get_assessment_questions, 
         name='get_assessment_questions'),
]