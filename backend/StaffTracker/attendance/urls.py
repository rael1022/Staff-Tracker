# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/trainer/trainings/', views.trainer_training_list, name='trainer_trainings'),
    path('api/trainer/generate-qr/', views.generate_qr_code, name='generate_qr'),
    path('api/trainer/attendance/<str:training_id>/', views.get_training_attendance, name='training_attendance'),
    path('api/trainer/manual-checkin/', views.manual_checkin, name='manual_checkin'),
    
    path('api/employee/qr-checkin/', views.qr_checkin, name='qr_checkin'),
]