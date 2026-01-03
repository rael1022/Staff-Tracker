from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('certificate-expiry/', views.certificate_expiry_report, name='certificate_expiry'),
    path('cpd-summary/', views.cpd_summary_report, name='cpd_summary'),
    path('attendance-summary/', views.attendance_summary_report, name='attendance_summary'),
    path('hod-department-training-progress/', views.hod_department_training_progress, name='hod_department_training_progress'),
    path('hod-department-report/', views.hod_department_report, name='hod_department_report'),
]