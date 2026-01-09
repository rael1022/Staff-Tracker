from django.urls import path
from . import views
from .views import hr_delete_certificate

urlpatterns = [
    # Employee
    path('my-certificates/', views.certificate_list, name='my_certificates'),

    # Trainer – new certificate flow
    path('trainer/certificates/', views.trainer_certificates_dashboard, name='trainer_certificates_dashboard'),
    path('trainer/provide/<int:training_id>/<int:user_id>/', views.provide_certificate, name='provide_certificate'),
    path('trainer/certificate/<int:cert_id>/edit-expiry/', views.edit_certificate_expiry, name='edit_certificate_expiry'),

    # Common
    path('preview/<int:pk>/', views.certificate_preview, name='certificate_preview'),

    # HR
    path('hr/delete/<int:cert_id>/', hr_delete_certificate, name='hr_delete_certificate'),
]
