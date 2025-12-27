from django.urls import path
from .views import my_cpd

urlpatterns = [
    path('my-cpd/', my_cpd, name='my_cpd'),
]