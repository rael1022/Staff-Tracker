from django.urls import path
from . import views

urlpatterns = [
    path('trainer/', views.trainer_dashboard, name='trainer_dashboard'),
    path('trainer/create/', views.create_training, name='create_training'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/register/<int:training_id>/', views.register_training, name='register_training'),
    path('trainer/edit/<int:training_id>/', views.edit_training, name='edit_training'),
    path('trainer/delete/<int:training_id>/', views.delete_training, name='delete_training'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/approve/<int:reg_id>/', views.approve_registration, name='approve_registration'),
    path('hod/reject/<int:reg_id>/', views.reject_registration, name='reject_registration'),
]
