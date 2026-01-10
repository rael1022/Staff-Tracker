from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hod',
    )
    search_fields = (
        'name',
        'hod__username',
    )
    ordering = ('name',)
    fieldsets = (
        ('Department Information', {
            'fields': ('name', 'hod')
        }),
    )
