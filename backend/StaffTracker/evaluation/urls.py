from django.urls import path
from . import views

urlpatterns = [
    path('submit/<int:training_id>/', views.submit_evaluation, name='submit_evaluation'),
    path('trainer/evaluations/', views.trainer_evaluations, name='trainer_evaluations'),
    path('trainer/evaluations/<int:training_id>/', views.trainer_evaluations, name='trainer_evaluation_detail'),
]