from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('certificate-expiry/', views.certificate_expiry_report, name='certificate_expiry'),
    path('cpd-summary/', views.cpd_summary_report, name='cpd_summary'),
    path('attendance-summary/', views.attendance_summary_report, name='attendance_summary'),
]