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

    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/create/', views.hr_create_training, name='hr_create_training'),
    path('hr/edit/<int:training_id>/', views.hr_edit_training, name='hr_edit_training'),
    path('hr/delete/<int:training_id>/', views.hr_delete_training, name='hr_delete_training'),
    path('hr/training/registrations/', views.hr_training_registrations, name='hr_training_registrations'),

    path('trainer/completions/', views.trainer_completions, name='trainer_completions'),
    path('trainer/complete-registration/<int:reg_id>/', views.complete_registration, name='complete_registration'),
]
