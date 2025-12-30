from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('generate-qr/', views.generate_qr_code, name='generate_qr'),
    path('scan/', views.scan_qr_code, name='scan_qr'),
    path('verify/', views.verify_user_and_checkin, name='verify_checkin'),
    path('training/<str:training_id>/', views.get_attendance_by_training, name='training_attendance'),
    path('all/', views.get_all_attendances, name='all_attendances'),
    
    # Trainer dashboard URLs
    path('frontend/trainer/trainings/', views.trainer_training_list, name='trainer_training_list'),
    path('frontend/trainer/generate-qr/<int:training_id>/', views.generate_qr_for_training, name='generate_qr_page'),
    
    path('trainer/', TemplateView.as_view(template_name='attendance/trainer_qr.html'), name='trainer_qr'),
    path('employee/', TemplateView.as_view(template_name='attendance/employee_checkin.html'), name='employee_checkin'),
]