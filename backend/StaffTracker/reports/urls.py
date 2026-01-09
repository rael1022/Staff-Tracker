from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('hr/certificates/', views.hr_certificate_report,name='hr_certificate_report'),
    path('cpd-summary/', views.cpd_summary_report, name='cpd_summary'),
    path('cpd-summary/download/', views.cpd_summary_download, name='cpd_summary_download'),
    path('attendance-summary/', views.attendance_summary_report, name='attendance_summary'),
    path('hod-department-training-progress/', views.hod_department_training_progress, name='hod_department_training_progress'),
    path('hod/department-report/', views.hod_department_report, name='hod_department_report'),
    path('hod/department-report/attendance/', views.hod_department_attendancereport, name='hod_department_attendancereport'),
    path('hod/department-report/cpd/', views.hod_department_cpdreport, name='hod_department_cpdreport'),
    path('hod/department-report/attendance/download/', views.hod_department_attendance_download, name='hod_department_attendance_download'),
    path('hod/department-report/cpd/download/', views.hod_department_cpd_download, name='hod_department_cpd_download'),
]