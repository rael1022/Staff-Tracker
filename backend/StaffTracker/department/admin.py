from django.contrib import admin
from django.contrib.auth.models import User
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'hod_name')
    search_fields = ('name', 'hod__username')
    ordering = ('name',)

    fieldsets = (
        ('Department Information', {
            'fields': ('name', 'hod')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'hod':
            hod_users = User.objects.filter(
                userprofile__role='HOD'
            )
            kwargs['queryset'] = hod_users
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def hod_name(self, obj):
        return obj.hod.username if obj.hod else '-'
    hod_name.short_description = 'HOD'
