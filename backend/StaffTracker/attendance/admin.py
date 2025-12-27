from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'training_id', 'status', 'date', 'check_in_time', 'is_qr_used']
    list_filter = ['status', 'date', 'is_qr_used']
    search_fields = ['user_id', 'training_id']
    readonly_fields = ['id']  
    
    list_per_page = 20
    
    date_hierarchy = 'date'