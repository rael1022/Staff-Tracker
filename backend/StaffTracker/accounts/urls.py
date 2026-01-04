from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('hr/create-user/', views.hr_create_user, name='hr_create_user'),
    path('hr/update-user/<int:user_id>/', views.hr_update_user, name='hr_update_user'),
    path('dashboard/delete_user/<int:user_id>/', views.hr_delete_user, name='hr_delete_user'),
    path('hr/toggle-user/<int:user_id>/', views.hr_toggle_user, name='hr_toggle_user'),
]
