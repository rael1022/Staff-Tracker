from django.urls import path
from . import views
from .views import hr_delete_certificate

urlpatterns = [
    path('my-certificates/', views.certificate_list, name='my_certificates'),
    path('issued/', views.issued_certificates, name='issued_certificates'),
    path('preview/<int:pk>/', views.certificate_preview, name='certificate_preview'),

    path('hr/delete/<int:cert_id>/', hr_delete_certificate, name='hr_delete_certificate'),
]