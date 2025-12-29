from django.urls import path
from . import views

urlpatterns = [
    path('pre/<int:training_id>/', views.create_pre_assessment, name='pre_assessment'),
    path('post/<int:training_id>/', views.create_post_assessment, name='post_assessment'),
]