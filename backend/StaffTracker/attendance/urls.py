# attendance/urls.py
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('api/trainer/trainings/', views.trainer_training_list, name='trainer_trainings'),
    path('api/trainer/generate-qr/', views.generate_qr_code, name='generate_qr'),
    path('api/trainer/attendance/<str:training_id>/', views.get_training_attendance, name='training_attendance'),
    path('api/trainer/manual-checkin/', views.manual_checkin, name='manual_checkin'),
    
    path('api/employee/qr-checkin/', views.qr_checkin, name='qr_checkin'),
    
    path('checkin/', views.checkin_page_view, name='checkin_page'),
    
    path('trainer/trainings/', TemplateView.as_view(template_name='trainer/trainer_trainings.html'), name='trainer_trainings_page'),
    path('test-attendance/', TemplateView.as_view(template_name='attendance/test_attendance.html'), name='test_attendance'),
]