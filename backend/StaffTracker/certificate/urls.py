from django.urls import path
from . import views

urlpatterns = [
    path('my-certificates/', views.certificate_list, name='my_certificates'),
    path('issued/', views.issued_certificates, name='issued_certificates'),
    path('preview/<int:pk>/', views.certificate_preview, name='certificate_preview'),
]