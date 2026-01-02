from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluation_dashboard, name='evaluation_dashboard'),
    path('submit/<int:training_id>/', views.submit_evaluation, name='submit_evaluation'),
]